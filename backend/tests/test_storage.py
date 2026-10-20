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


def test_count_anomalies_detects_malformed_shard_directory(storage) -> None:
    malformed = storage.normalized_dir / "notshard"
    malformed.mkdir(parents=True, exist_ok=True)
    (malformed / "whatever.bin").write_bytes(b"x")

    assert storage.count_normalized_anomalies() == 1
    assert storage.sweep_normalized(set()) == 0
    assert (malformed / "whatever.bin").exists()


def test_count_anomalies_detects_wrong_shard_key(storage) -> None:
    key = "ab" + "0" * 30
    wrong_shard = storage.normalized_dir / "cd"
    wrong_shard.mkdir(parents=True, exist_ok=True)
    (wrong_shard / key).write_bytes(b"x")

    assert storage.count_normalized_anomalies() == 1
    assert storage.sweep_normalized(set()) == 0
    assert (wrong_shard / key).exists()


def test_count_anomalies_detects_nested_entry(storage) -> None:
    shard = storage.normalized_dir / "ab"
    shard.mkdir(parents=True, exist_ok=True)
    nested = shard / "nested"
    nested.mkdir()
    (nested / "x").write_bytes(b"x")

    assert storage.count_normalized_anomalies() == 1
    assert storage.sweep_normalized(set()) == 0
    assert (nested / "x").exists()


def test_sweep_skips_anomalies_but_removes_genuine_orphans(storage) -> None:
    wrong_key = "ab" + "0" * 30
    wrong_shard = storage.normalized_dir / "cd"
    wrong_shard.mkdir(parents=True, exist_ok=True)
    (wrong_shard / wrong_key).write_bytes(b"x")

    orphan_key = storage.new_key()
    storage.write_normalized(orphan_key, b"orphan")

    removed = storage.sweep_normalized(set())

    assert removed == 1
    assert not storage.exists(orphan_key)
    assert (wrong_shard / wrong_key).exists()
    assert storage.count_normalized_anomalies() == 1
