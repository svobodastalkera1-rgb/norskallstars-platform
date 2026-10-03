"""Vendor-independent async object boundary and development-only safe local adapter."""

import asyncio
import os
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Protocol


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
            temporary = ".write-" + uuid.uuid4().hex
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
