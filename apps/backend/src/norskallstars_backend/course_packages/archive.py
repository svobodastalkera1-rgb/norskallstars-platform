"""Bounded in-memory ZIP reading; never extract attacker-controlled paths."""

import io
import re
import stat
import struct
import zipfile
import zlib


class BoundaryError(ValueError):
    """Safe error code only; never carry package content or filesystem paths."""


def safe_path(name: str) -> bool:
    return (
        len(name) <= 240
        and re.fullmatch(r"[A-Za-z0-9_./-]+", name) is not None
        and all(p and not p.startswith(".") and not p.endswith(".") for p in name.split("/"))
        and all(
            p.split(".")[0].upper() not in {"CON", "PRN", "AUX", "NUL"}
            and not re.fullmatch(r"(?:COM|LPT)[1-9]", p.split(".")[0].upper())
            for p in name.split("/")
        )
    )


def central_preflight(data: bytes, entries: int) -> None:
    # Count bounded central records BEFORE ZipFile constructs its entry objects.
    # Multidisk/ZIP64 are unnecessary at Contract v1's limits and rejected explicitly.
    end = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    if end < 0 or end + 22 > len(data):
        raise BoundaryError("invalid_archive")
    disk, directory_disk, on_disk, count, size, offset, comment = struct.unpack_from(
        "<4H2IH", data, end + 4
    )
    if disk or directory_disk or on_disk != count or count == 65535 or count > entries:
        raise BoundaryError("entry_count")
    if offset + size != end or end + 22 + comment != len(data):
        raise BoundaryError("archive_directory")
    cursor = offset
    actual = 0
    while cursor < end:
        if data[cursor : cursor + 4] != b"PK\x01\x02" or cursor + 46 > end:
            raise BoundaryError("archive_directory")
        name, extra, annotation = struct.unpack_from("<3H", data, cursor + 28)
        cursor += 46 + name + extra + annotation
        actual += 1
        if actual > entries or cursor > end:
            raise BoundaryError("entry_count")
    if actual != count:
        raise BoundaryError("entry_count")


def read_archive(
    data: bytes,
    *,
    entries: int = 2000,
    total_limit: int = 128 << 20,
    file_limit: int = 32 << 20,
    archive_limit: int = 64 << 20,
) -> dict[str, bytes]:
    if len(data) > archive_limit:
        raise BoundaryError("archive_size")
    try:
        central_preflight(data, entries)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > entries:
                raise BoundaryError("entry_count")
            seen: set[str] = set()
            total = 0
            for info in infos:
                name = info.filename
                mode = stat.S_IFMT(info.external_attr >> 16)
                if name != info.orig_filename or not safe_path(name) or name.casefold() in seen:
                    raise BoundaryError("archive_path")
                seen.add(name.casefold())
                if (
                    info.is_dir()
                    or mode not in (0, stat.S_IFREG)
                    or info.flag_bits & 1
                    or info.external_attr & 0x10
                    or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                ):
                    raise BoundaryError("archive_type")
                total += info.file_size
                if (
                    info.file_size > file_limit
                    or total > total_limit
                    or info.file_size > max(info.compress_size, 1) * 100
                ):
                    raise BoundaryError("archive_expansion")
            result = {}
            for info in infos:
                with archive.open(info) as stream:
                    payload = stream.read(file_limit + 1)
                    if len(payload) != info.file_size or len(payload) > file_limit:
                        raise BoundaryError("entry_size")
                    result[info.filename] = payload
            return result
    except (
        zipfile.BadZipFile,
        RuntimeError,
        OSError,
        NotImplementedError,
        struct.error,
        zlib.error,
    ) as exc:
        raise BoundaryError("invalid_archive") from exc
