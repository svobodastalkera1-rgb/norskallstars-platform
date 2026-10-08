"""Vendor-independent async object boundary and development-only safe local adapter."""

import asyncio
import os
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from norskallstars_backend.config import Settings


class ObjectStorage(Protocol):
    async def put(self, key: str, data: bytes) -> None: ...
    async def get(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> None: ...


def validate_key(key: str) -> list[str]:
    parts = key.split("/")
    if (
        len(key) > 512
        or not key
        or PurePosixPath(key).is_absolute()
        or any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", part) for part in parts)
        or any(part in (".", "..") for part in parts)
    ):
        raise ValueError("Invalid object key")
    return parts


class LocalObjectStorage:
    """Linux/POSIX development storage; directory descriptors prevent symlink escape."""

    def __init__(self, root: Path, max_bytes: int) -> None:
        if not root.is_absolute() or not root.is_dir() or root.is_symlink():
            raise ValueError("Local storage root must be an existing absolute nonsymlink directory")
        if not 1 <= max_bytes <= 104_857_600:
            raise ValueError("Object size limit must be explicitly bounded")
        self.root = root
        self.max_bytes = max_bytes

    @contextmanager
    def _parent(self, parts: list[str], create: bool = False) -> Iterator[int]:
        descriptor = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                if create:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=descriptor)
                    except FileExistsError:
                        pass
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
                )
                os.close(descriptor)
                descriptor = child
            yield descriptor
        finally:
            os.close(descriptor)

    def _put(self, key: str, data: bytes) -> None:
        parts = validate_key(key)
        if len(data) > self.max_bytes:
            raise ValueError("Object exceeds configured size limit")
        with self._parent(parts, create=True) as parent:
            temporary = "write-" + uuid.uuid4().hex
            descriptor = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode=0o600,
                dir_fd=parent,
            )
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, parts[-1], src_dir_fd=parent, dst_dir_fd=parent)
            finally:
                try:
                    os.unlink(temporary, dir_fd=parent)
                except FileNotFoundError:
                    pass

    def _get(self, key: str) -> bytes:
        parts = validate_key(key)
        with self._parent(parts) as parent:
            descriptor = os.open(
                parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
            import stat

            with os.fdopen(descriptor, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError("Object is not a regular file")
                data = stream.read(self.max_bytes + 1)
                if len(data) > self.max_bytes:
                    raise ValueError("Object exceeds configured size limit")
                return data

    def _delete(self, key: str) -> None:
        parts = validate_key(key)
        try:
            with self._parent(parts) as parent:
                os.unlink(parts[-1], dir_fd=parent)
        except FileNotFoundError:
            pass  # idempotent deletion

    async def put(self, key: str, data: bytes) -> None:
        await asyncio.to_thread(self._put, key, data)

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._get, key)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._delete, key)


class StoredObject:
    def __init__(self, key: str, modified_at: float) -> None:
        self.key, self.modified_at = key, modified_at


class InventoryStorage(ObjectStorage, Protocol):
    async def inventory(self) -> list[StoredObject]: ...


def _local_inventory(storage: LocalObjectStorage) -> list[StoredObject]:
    import stat

    result: list[StoredObject] = []
    # Never follow symlinks; traversal is bounded and only owned namespaces are scanned.
    for directory, directories, files in os.walk(storage.root, followlinks=False):
        directories[:] = [d for d in directories if not (Path(directory) / d).is_symlink()]
        for name in files:
            path = Path(directory) / name
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                continue
            key = path.relative_to(storage.root).as_posix()
            if key.startswith(("releases/", "recordings/")) and not name.startswith(".write-"):
                validate_key(key)
                result.append(StoredObject(key, info.st_mtime))
                if len(result) > 100000:
                    raise ValueError("Storage inventory exceeds resource budget")
    return result


class InventoriedLocalStorage(LocalObjectStorage):
    async def inventory(self) -> list[StoredObject]:
        return await asyncio.to_thread(_local_inventory, self)


class S3ObjectStorage:
    """Private S3-compatible storage; bounded calls, TLS verification, no signed URLs."""

    def __init__(self, settings: "Settings") -> None:
        import boto3
        from botocore.config import Config

        self.max_bytes = settings.storage_max_bytes
        self.bucket = settings.s3_bucket or ""
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key.get_secret_value()
            if settings.s3_access_key
            else None,
            aws_secret_access_key=settings.s3_secret_key.get_secret_value()
            if settings.s3_secret_key
            else None,
            config=Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 2}),
        )

    def _ensure_unversioned(self) -> None:
        # Delete markers are insufficient for personal-data erasure. A suspended
        # bucket can still retain old versions, so neither enabled nor suspended
        # versioning is accepted by this current-key reconciliation adapter.
        state = self.client.get_bucket_versioning(Bucket=self.bucket)
        if state.get("Status") is not None:
            raise ValueError("Current storage adapter requires an unversioned private bucket")

    async def put(self, key: str, data: bytes) -> None:
        validate_key(key)
        if len(data) > self.max_bytes:
            raise ValueError("Object exceeds configured size limit")
        await asyncio.to_thread(self._ensure_unversioned)
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ServerSideEncryption="AES256",
        )

    def _get(self, key: str) -> bytes:
        validate_key(key)
        self._ensure_unversioned()
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        stream = response["Body"]
        try:
            if response["ContentLength"] > self.max_bytes:
                raise ValueError("Object exceeds configured size limit")
            data = stream.read(self.max_bytes + 1)
            if len(data) > self.max_bytes:
                raise ValueError("Object exceeds configured size limit")
            return data
        finally:
            stream.close()

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._get, key)

    async def delete(self, key: str) -> None:
        validate_key(key)
        await asyncio.to_thread(self._ensure_unversioned)
        await asyncio.to_thread(self.client.delete_object, Bucket=self.bucket, Key=key)

    def _inventory(self) -> list[StoredObject]:
        self._ensure_unversioned()
        result: list[StoredObject] = []
        for prefix in ("releases/", "recordings/"):
            for page in self.client.get_paginator("list_objects_v2").paginate(
                Bucket=self.bucket,
                Prefix=prefix,
                PaginationConfig={"PageSize": 1000},
            ):
                for obj in page.get("Contents", []):
                    validate_key(obj["Key"])
                    result.append(StoredObject(obj["Key"], obj["LastModified"].timestamp()))
                    if len(result) > 100000:
                        raise ValueError("Storage inventory exceeds resource budget")
        return result

    async def inventory(self) -> list[StoredObject]:
        return await asyncio.to_thread(self._inventory)


def create_storage(settings: "Settings") -> InventoryStorage | None:
    if settings.storage_backend == "local" and settings.storage_root:
        return InventoriedLocalStorage(settings.storage_root, settings.storage_max_bytes)
    if settings.storage_backend == "s3":
        return S3ObjectStorage(settings)
    return None
