import time

import pytest

from app.storage import PhotoStorage, StorageError


@pytest.fixture()
def storage(tmp_path) -> PhotoStorage:
    photo_storage = PhotoStorage(tmp_path / "photos")
    photo_storage.ensure_dirs()
    return photo_storage


def test_write_and_read_round_trip(storage) -> None:
    key = storage.new_key()
    storage.write_normalized(key, b"normalized-bytes")

    assert storage.read_normalized(key) == b"normalized-bytes"
    assert storage.exists(key)


def test_new_key_is_opaque_hex(storage) -> None:
    key = storage.new_key()
    assert len(key) == 32
    assert int(key, 16) >= 0


def test_write_rejects_traversal_key(storage) -> None:
    with pytest.raises(StorageError):
        storage.write_normalized("../outside", b"data")


def test_read_missing_key_raises(storage) -> None:
    with pytest.raises(StorageError):
        storage.read_normalized(storage.new_key())


def test_delete_is_idempotent(storage) -> None:
    key = storage.new_key()
    storage.write_normalized(key, b"data")

    storage.delete_normalized(key)
    storage.delete_normalized(key)

    assert not storage.exists(key)


def test_sweep_removes_only_unreferenced_files(storage) -> None:
    keep = storage.new_key()
    drop = storage.new_key()
    storage.write_normalized(keep, b"keep")
    storage.write_normalized(drop, b"drop")

    removed = storage.sweep_normalized({keep})

    assert removed == 1
    assert storage.exists(keep)
    assert not storage.exists(drop)


def test_sweep_removes_stale_atomic_write_partial(storage) -> None:
    key = storage.new_key()
    partial = storage._normalized_path(key).with_name(key + ".part")
    partial.parent.mkdir(parents=True)
    partial.write_bytes(b"partial")

    assert storage.sweep_normalized(set()) == 1
    assert not partial.exists()


def test_sweep_tmp_removes_stale_files(storage) -> None:
    stale = storage.new_tmp_path()
    stale.write_bytes(b"stale")

    past = time.time() - 7200
    import os

    os.utime(stale, (past, past))

    removed = storage.sweep_tmp(max_age_seconds=3600)

    assert removed == 1
    assert not stale.exists()
