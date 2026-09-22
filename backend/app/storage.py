import os
import re
import time
import uuid
from pathlib import Path

_NORMALIZED_KEY_PATTERN = re.compile(r"^[0-9a-f]{32}$")

_TMP_SUFFIX = ".part"


class StorageError(Exception):
    """Raised when a private-storage operation cannot be completed."""


class PhotoStorage:
    """Owns normalized-image bytes outside the public web root.

    Keys are server-generated opaque UUID hex strings. Files are sharded by
    their first two characters to avoid a single oversized directory.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.normalized_dir = root / "normalized"
        self.tmp_dir = root / "tmp"

    def ensure_dirs(self) -> None:
        self.normalized_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.tmp_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def new_key(self) -> str:
        return uuid.uuid4().hex

    def _normalized_path(self, key: str) -> Path:
        if _NORMALIZED_KEY_PATTERN.fullmatch(key) is None:
            raise StorageError("invalid storage key")
        return self.normalized_dir / key[:2] / key

    def write_normalized(self, key: str, data: bytes) -> None:
        path = self._normalized_path(key)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = path.with_name(path.name + _TMP_SUFFIX)
        temporary.write_bytes(data)
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)

    def read_normalized(self, key: str) -> bytes:
        path = self._normalized_path(key)
        if not path.is_file():
            raise StorageError("missing file")
        return path.read_bytes()

    def exists(self, key: str) -> bool:
        return self._normalized_path(key).is_file()

    def delete_normalized(self, key: str) -> None:
        path = self._normalized_path(key)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError("delete failed") from exc
        self._prune_empty_shards(path)

    def new_tmp_path(self) -> Path:
        return self.tmp_dir / (uuid.uuid4().hex + ".tmp")

    def delete_tmp(self, path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError("temporary delete failed") from exc

    def _prune_empty_shards(self, removed: Path) -> None:
        shard = removed.parent
        if shard != self.normalized_dir and shard.exists():
            try:
                shard.rmdir()
            except OSError:
                pass

    def sweep_normalized(
        self,
        valid_keys: set[str],
        min_age_seconds: int = 0,
        now_timestamp: float | None = None,
    ) -> int:
        """Delete normalized files whose key is no longer referenced.

        Files newer than ``min_age_seconds`` are left alone so a cleanup pass
        cannot race a database transaction that has written its derivative but
        has not committed the corresponding row yet. Stale atomic-write partials
        are removed by the same pass.
        """
        removed = 0
        current_timestamp = now_timestamp if now_timestamp is not None else time.time()
        if not self.normalized_dir.exists():
            return 0
        for entry in self.normalized_dir.iterdir():
            if not entry.is_dir():
                continue
            for file in entry.iterdir():
                if not file.is_file():
                    continue
                key = file.name.removesuffix(_TMP_SUFFIX)
                is_normalized = _NORMALIZED_KEY_PATTERN.fullmatch(file.name) is not None
                is_partial = (
                    file.name.endswith(_TMP_SUFFIX)
                    and _NORMALIZED_KEY_PATTERN.fullmatch(key) is not None
                )
                if not is_normalized and not is_partial:
                    continue
                try:
                    if (
                        min_age_seconds > 0
                        and current_timestamp - file.stat().st_mtime < min_age_seconds
                    ):
                        continue
                    if is_partial or file.name not in valid_keys:
                        file.unlink(missing_ok=True)
                        removed += 1
                except OSError:
                    continue
            try:
                entry.rmdir()
            except OSError:
                pass
        return removed

    def sweep_tmp(self, max_age_seconds: int, now_timestamp: float | None = None) -> int:
        """Delete stale temporary raw-upload files older than the given age."""
        removed = 0
        if not self.tmp_dir.exists():
            return 0
        current_timestamp = now_timestamp if now_timestamp is not None else time.time()
        cutoff = current_timestamp - max_age_seconds
        for entry in self.tmp_dir.iterdir():
            if entry.is_file():
                try:
                    if entry.stat().st_mtime < cutoff:
                        entry.unlink(missing_ok=True)
                        removed += 1
                except OSError:
                    continue
        return removed
