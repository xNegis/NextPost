import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from app.config import Settings

_NORMALIZED_KEY_PATTERN = re.compile(r"^[0-9a-f]{32}$")

_SHARD_PATTERN = re.compile(r"^[0-9a-f]{2}$")

_TMP_SUFFIX = ".part"

_S3_DELETE_BATCH_SIZE = 1000


def _validate_normalized_key(key: str) -> None:
    if _NORMALIZED_KEY_PATTERN.fullmatch(key) is None:
        raise StorageError("invalid storage key")


def _classify_normalized_file(shard_name: str, name: str) -> str:
    """Classify a file name within a shard directory as ``key``, ``partial`` or ``anomaly``.

    A valid key or atomic-write partial must also live in the shard matching its first two
    characters; a valid-looking key stored under the wrong shard is an anomaly.
    """
    if _NORMALIZED_KEY_PATTERN.fullmatch(name) is not None:
        return "key" if name[:2] == shard_name else "anomaly"
    if name.endswith(_TMP_SUFFIX):
        stripped = name.removesuffix(_TMP_SUFFIX)
        if _NORMALIZED_KEY_PATTERN.fullmatch(stripped) is not None:
            return "partial" if stripped[:2] == shard_name else "anomaly"
    return "anomaly"


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
        _validate_normalized_key(key)
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
        are removed by the same pass. Malformed shard directories, symlinks,
        nested entries and keys stored under the wrong shard are never deleted.
        """
        removed = 0
        current_timestamp = now_timestamp if now_timestamp is not None else time.time()
        if not self.normalized_dir.exists():
            return 0
        for entry in self.normalized_dir.iterdir():
            if entry.is_symlink() or not entry.is_dir():
                continue
            if _SHARD_PATTERN.fullmatch(entry.name) is None:
                continue
            for file in entry.iterdir():
                if file.is_symlink() or not file.is_file():
                    continue
                kind = _classify_normalized_file(entry.name, file.name)
                if kind == "anomaly":
                    continue
                try:
                    if (
                        min_age_seconds > 0
                        and current_timestamp - file.stat().st_mtime < min_age_seconds
                    ):
                        continue
                    if kind == "partial" or file.name not in valid_keys:
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

    def count_normalized_anomalies(self) -> int:
        """Count unexpected objects under the normalized root without deleting them.

        A valid object is a 32-hex-key file (or its ``.part`` atomic-write partial) inside the
        matching two-character shard directory. Malformed shard directories, symlinks, nested or
        unexpected entries, non-key/partial files, and valid-looking keys stored under the wrong
        shard are anomalies left untouched for restricted operator handling.
        """
        anomalies = 0
        if not self.normalized_dir.exists():
            return 0
        try:
            entries = list(self.normalized_dir.iterdir())
        except OSError:
            return 1
        for entry in entries:
            if entry.is_symlink() or not entry.is_dir():
                anomalies += 1
                continue
            if _SHARD_PATTERN.fullmatch(entry.name) is None:
                anomalies += 1
                continue
            try:
                files = list(entry.iterdir())
            except OSError:
                anomalies += 1
                continue
            for file in files:
                if file.is_symlink():
                    anomalies += 1
                    continue
                if not file.is_file():
                    anomalies += 1
                    continue
                if _classify_normalized_file(entry.name, file.name) == "anomaly":
                    anomalies += 1
        return anomalies


class S3PhotoStorage(PhotoStorage):
    """Private normalized-photo storage under one fixed S3 namespace.

    Raw uploads remain temporary local files. Normalized object deletion enumerates and deletes
    every exact version and delete marker before it can report success.
    """

    def __init__(
        self,
        *,
        root: Path,
        region: str,
        bucket: str,
        prefix: str = "nextpost",
        client: Any | None = None,
    ) -> None:
        super().__init__(root)
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        if self.prefix != "nextpost":
            raise StorageError("invalid S3 prefix")
        self._client: Any = client or boto3.client("s3", region_name=region)

    def ensure_dirs(self) -> None:
        self.tmp_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _object_key(self, key: str) -> str:
        _validate_normalized_key(key)
        return f"{self.prefix}/normalized/{key[:2]}/{key}"

    def write_normalized(self, key: str, data: bytes) -> None:
        object_key = self._object_key(key)
        try:
            self._client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=data,
                ContentType="image/jpeg",
                ServerSideEncryption="AES256",
            )
        except Exception as exc:
            raise StorageError("write failed") from exc

    def read_normalized(self, key: str) -> bytes:
        object_key = self._object_key(key)
        try:
            response = self._client.get_object(Bucket=self.bucket, Key=object_key)
            body = response["Body"].read()
        except Exception as exc:
            raise StorageError("missing or unreadable object") from exc
        if not isinstance(body, bytes):
            raise StorageError("invalid object body")
        return body

    @staticmethod
    def _is_missing(exc: ClientError) -> bool:
        error = exc.response.get("Error", {})
        return str(error.get("Code", "")) in {"404", "NoSuchKey", "NotFound"}

    def exists(self, key: str) -> bool:
        object_key = self._object_key(key)
        try:
            self._client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as exc:
            if self._is_missing(exc):
                return False
            raise StorageError("head failed") from exc
        except Exception as exc:
            raise StorageError("head failed") from exc

    def _list_exact_versions(self, object_key: str) -> list[dict[str, str]]:
        found: list[dict[str, str]] = []
        request: dict[str, Any] = {
            "Bucket": self.bucket,
            "Prefix": object_key,
            "MaxKeys": 1000,
        }
        for _ in range(1000):
            try:
                response = self._client.list_object_versions(**request)
            except Exception as exc:
                raise StorageError("version inventory failed") from exc
            for collection in ("Versions", "DeleteMarkers"):
                for item in response.get(collection, []):
                    if item.get("Key") == object_key and isinstance(item.get("VersionId"), str):
                        found.append({"Key": object_key, "VersionId": item["VersionId"]})
            if not response.get("IsTruncated", False):
                return found
            next_key = response.get("NextKeyMarker")
            next_version = response.get("NextVersionIdMarker")
            if not isinstance(next_key, str) or not isinstance(next_version, str):
                raise StorageError("invalid version inventory cursor")
            request["KeyMarker"] = next_key
            request["VersionIdMarker"] = next_version
        raise StorageError("version inventory page limit exceeded")

    def delete_normalized(self, key: str) -> None:
        object_key = self._object_key(key)
        versions = self._list_exact_versions(object_key)
        try:
            if versions:
                for offset in range(0, len(versions), _S3_DELETE_BATCH_SIZE):
                    response = self._client.delete_objects(
                        Bucket=self.bucket,
                        Delete={
                            "Objects": versions[offset : offset + _S3_DELETE_BATCH_SIZE],
                            "Quiet": True,
                        },
                    )
                    if response.get("Errors"):
                        raise StorageError("version delete failed")
            else:
                self._client.delete_object(Bucket=self.bucket, Key=object_key)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError("delete failed") from exc
        if self._list_exact_versions(object_key) or self.exists(key):
            raise StorageError("delete verification failed")

    def _list_current_objects(self) -> list[dict[str, Any]]:
        base_prefix = f"{self.prefix}/normalized/"
        request: dict[str, Any] = {
            "Bucket": self.bucket,
            "Prefix": base_prefix,
            "MaxKeys": 1000,
        }
        objects: list[dict[str, Any]] = []
        for _ in range(1000):
            try:
                response = self._client.list_objects_v2(**request)
            except Exception as exc:
                raise StorageError("object inventory failed") from exc
            objects.extend(response.get("Contents", []))
            if not response.get("IsTruncated", False):
                return objects
            token = response.get("NextContinuationToken")
            if not isinstance(token, str):
                raise StorageError("invalid object inventory cursor")
            request["ContinuationToken"] = token
        raise StorageError("object inventory page limit exceeded")

    def _key_from_object(self, object_key: object) -> str | None:
        if not isinstance(object_key, str):
            return None
        base = f"{self.prefix}/normalized/"
        if not object_key.startswith(base):
            return None
        relative = object_key.removeprefix(base)
        parts = relative.split("/")
        if len(parts) != 2 or parts[0] != parts[1][:2]:
            return None
        return parts[1] if _NORMALIZED_KEY_PATTERN.fullmatch(parts[1]) else None

    def sweep_normalized(
        self,
        valid_keys: set[str],
        min_age_seconds: int = 0,
        now_timestamp: float | None = None,
    ) -> int:
        current_timestamp = now_timestamp if now_timestamp is not None else time.time()
        removed = 0
        for item in self._list_current_objects():
            key = self._key_from_object(item.get("Key"))
            if key is None or key in valid_keys:
                continue
            last_modified = item.get("LastModified")
            timestamp_method = getattr(last_modified, "timestamp", None)
            if min_age_seconds > 0 and callable(timestamp_method):
                if current_timestamp - float(timestamp_method()) < min_age_seconds:
                    continue
            self.delete_normalized(key)
            removed += 1
        return removed

    def count_normalized_anomalies(self) -> int:
        return sum(
            1
            for item in self._list_current_objects()
            if self._key_from_object(item.get("Key")) is None
        )


def build_photo_storage(settings: Settings, *, client: Any | None = None) -> PhotoStorage:
    if settings.photo_storage_backend == "filesystem":
        storage: PhotoStorage = PhotoStorage(settings.photo_storage_root)
    else:
        if settings.s3_region is None or settings.s3_bucket is None:
            raise StorageError("S3 storage configuration is incomplete")
        storage = S3PhotoStorage(
            root=settings.photo_storage_root,
            region=settings.s3_region,
            bucket=settings.s3_bucket,
            prefix=settings.s3_prefix,
            client=client,
        )
    storage.ensure_dirs()
    return storage
