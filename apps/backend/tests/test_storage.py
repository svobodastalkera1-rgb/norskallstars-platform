from pathlib import Path

import pytest

from norskallstars_backend.storage import LocalObjectStorage


async def test_roundtrip_replace_and_idempotent_delete(tmp_path):
    storage = LocalObjectStorage(tmp_path, 100)
    await storage.put("synthetic/asset.txt", b"first")
    assert await storage.get("synthetic/asset.txt") == b"first"
    await storage.put("synthetic/asset.txt", b"second")
    assert await storage.get("synthetic/asset.txt") == b"second"
    await storage.delete("synthetic/asset.txt")
    await storage.delete("synthetic/asset.txt")
    with pytest.raises(FileNotFoundError):
        await storage.get("synthetic/asset.txt")


@pytest.mark.parametrize("key", ["../outside", "/absolute", "a/../b", "a//b", "a\\b", "a/./b", ""])
async def test_traversal_and_unsafe_keys_rejected(tmp_path, key):
    storage = LocalObjectStorage(tmp_path, 100)
    for operation in [storage.put(key, b"x"), storage.get(key), storage.delete(key)]:
        with pytest.raises(ValueError):
            await operation


async def test_oversized_objects_do_not_replace_existing_data(tmp_path):
    storage = LocalObjectStorage(tmp_path, 3)
    await storage.put("item", b"old")
    with pytest.raises(ValueError):
        await storage.put("item", b"large")
    assert await storage.get("item") == b"old"
    (tmp_path / "item").write_bytes(b"external-oversized")
    with pytest.raises(ValueError):
        await storage.get("item")


async def test_directory_and_leaf_symlinks_do_not_escape_root(tmp_path):
    root, outside = tmp_path / "root", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "item").write_bytes(b"outside")
    (root / "linked").symlink_to(outside, target_is_directory=True)
    (root / "leaf").symlink_to(outside / "item")
    storage = LocalObjectStorage(root, 100)
    with pytest.raises(OSError):
        await storage.put("linked/item", b"overwrite")
    with pytest.raises(OSError):
        await storage.get("leaf")
    await storage.put("leaf", b"safe replacement")
    assert (outside / "item").read_bytes() == b"outside"
    assert await storage.get("leaf") == b"safe replacement"


def test_root_must_be_explicit_and_existing(tmp_path):
    with pytest.raises(ValueError):
        LocalObjectStorage(Path("relative"), 10)
    with pytest.raises(ValueError):
        LocalObjectStorage(tmp_path / "missing", 10)


@pytest.mark.parametrize("limit", [0, -1, 104_857_601])
def test_size_limit_itself_is_validated(tmp_path, limit):
    with pytest.raises(ValueError):
        LocalObjectStorage(tmp_path, limit)
