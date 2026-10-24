from datetime import datetime, timezone
from io import BytesIO

import pytest
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from app.s3_preflight import inspect_bucket
from app.storage import S3PhotoStorage, StorageError


def _missing(operation: str = "HeadObject") -> ClientError:
    return ClientError({"Error": {"Code": "404", "Message": "missing"}}, operation)


class FakeS3:
    def __init__(self) -> None:
        self.versions: dict[str, list[tuple[str, bytes | None]]] = {}

    def put_object(self, **kwargs):
        key = kwargs["Key"]
        versions = self.versions.setdefault(key, [])
        versions.insert(0, (f"v{len(versions) + 1}", kwargs["Body"]))
        return {"VersionId": versions[0][0]}

    def get_object(self, **kwargs):
        for _version, body in self.versions.get(kwargs["Key"], []):
            if body is not None:
                return {"Body": BytesIO(body)}
            break
        raise _missing("GetObject")

    def head_object(self, **kwargs):
        for _version, body in self.versions.get(kwargs["Key"], []):
            if body is not None:
                return {}
            break
        raise _missing()

    def list_object_versions(self, **kwargs):
        prefix = kwargs["Prefix"]
        versions = []
        markers = []
        for key, values in self.versions.items():
            if not key.startswith(prefix):
                continue
            for version, body in values:
                target = markers if body is None else versions
                target.append({"Key": key, "VersionId": version})
        return {"Versions": versions, "DeleteMarkers": markers, "IsTruncated": False}

    def delete_objects(self, **kwargs):
        for item in kwargs["Delete"]["Objects"]:
            self.versions[item["Key"]] = [
                pair for pair in self.versions.get(item["Key"], []) if pair[0] != item["VersionId"]
            ]
        return {"Deleted": kwargs["Delete"]["Objects"]}

    def delete_object(self, **kwargs):
        self.versions.pop(kwargs["Key"], None)
        return {}

    def list_objects_v2(self, **kwargs):
        contents = []
        for key, values in self.versions.items():
            if key.startswith(kwargs["Prefix"]) and values and values[0][1] is not None:
                contents.append(
                    {"Key": key, "LastModified": datetime(2020, 1, 1, tzinfo=timezone.utc)}
                )
        return {"Contents": contents, "IsTruncated": False}


@pytest.fixture
def s3_storage(tmp_path):
    client = FakeS3()
    storage = S3PhotoStorage(
        root=tmp_path / "photos",
        region="eu-west-1",
        bucket="private-bucket",
        client=client,
    )
    storage.ensure_dirs()
    return storage, client


def test_s3_round_trip_and_permanent_version_deletion(s3_storage):
    storage, client = s3_storage
    key = storage.new_key()
    storage.write_normalized(key, b"first")
    storage.write_normalized(key, b"second")

    assert storage.read_normalized(key) == b"second"
    assert len(client.versions[storage._object_key(key)]) == 2

    storage.delete_normalized(key)

    assert not storage.exists(key)
    assert client.versions[storage._object_key(key)] == []


def test_s3_delete_marker_is_removed_too(s3_storage):
    storage, client = s3_storage
    key = storage.new_key()
    object_key = storage._object_key(key)
    client.versions[object_key] = [("marker", None), ("old", b"old")]

    storage.delete_normalized(key)

    assert client.versions[object_key] == []


def test_s3_prefix_and_inventory_are_bounded(s3_storage):
    storage, client = s3_storage
    keep = storage.new_key()
    drop = storage.new_key()
    storage.write_normalized(keep, b"keep")
    storage.write_normalized(drop, b"drop")
    client.versions["formcadence/normalized/aa/" + "a" * 32] = [("v1", b"foreign")]

    assert storage.sweep_normalized({keep}) == 1
    assert storage.exists(keep)
    assert not storage.exists(drop)
    assert "formcadence/normalized/aa/" + "a" * 32 in client.versions


def test_s3_rejects_invalid_key(s3_storage):
    storage, _client = s3_storage
    with pytest.raises(StorageError, match="invalid storage key"):
        storage.write_normalized("../escape", b"x")


class SafePreflightClient:
    def head_bucket(self, **_kwargs):
        return {}

    def get_public_access_block(self, **_kwargs):
        return {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            }
        }

    def get_bucket_policy_status(self, **_kwargs):
        return {"PolicyStatus": {"IsPublic": False}}

    def get_bucket_encryption(self, **_kwargs):
        return {"ServerSideEncryptionConfiguration": {"Rules": [{}]}}

    def get_bucket_versioning(self, **_kwargs):
        return {"Status": "Enabled"}

    def get_object_lock_configuration(self, **_kwargs):
        raise ClientError(
            {"Error": {"Code": "ObjectLockConfigurationNotFoundError"}},
            "GetObjectLockConfiguration",
        )

    def get_bucket_lifecycle_configuration(self, **_kwargs):
        raise ClientError(
            {"Error": {"Code": "NoSuchLifecycleConfiguration"}},
            "GetBucketLifecycleConfiguration",
        )

    def get_bucket_replication(self, **_kwargs):
        raise ClientError(
            {"Error": {"Code": "ReplicationConfigurationNotFoundError"}},
            "GetBucketReplication",
        )

    def list_object_versions(self, **_kwargs):
        return {"Versions": []}


def test_owner_preflight_accepts_safe_versioned_bucket():
    report = inspect_bucket(SafePreflightClient(), "private-bucket", "nextpost")
    assert report.compatible
    assert all(check.passed for check in report.checks)


def test_owner_preflight_accepts_absent_bucket_policy():
    client = SafePreflightClient()

    def missing_policy(**_kwargs):
        raise ClientError({"Error": {"Code": "NoSuchBucketPolicy"}}, "GetBucketPolicyStatus")

    client.get_bucket_policy_status = missing_policy

    report = inspect_bucket(client, "private-bucket", "nextpost")

    assert report.compatible
    assert any(
        check.name == "bucket-policy" and check.passed and check.detail == "not configured"
        for check in report.checks
    )


def test_owner_preflight_rejects_default_object_lock_retention():
    client = SafePreflightClient()
    client.get_object_lock_configuration = lambda **_kwargs: {
        "ObjectLockConfiguration": {
            "ObjectLockEnabled": "Enabled",
            "Rule": {"DefaultRetention": {"Days": 1}},
        }
    }
    report = inspect_bucket(client, "private-bucket", "nextpost")
    assert not report.compatible
    assert any(
        check.name == "object-lock-default-retention" and not check.passed
        for check in report.checks
    )
