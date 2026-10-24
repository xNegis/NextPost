"""Read-only owner preflight for the RF-42 private S3 activation gate."""

import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Callable

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class PreflightReport:
    compatible: bool
    checks: tuple[PreflightCheck, ...]


def _error_code(exc: ClientError) -> str:
    return str(exc.response.get("Error", {}).get("Code", "unknown"))


def _optional_configuration(
    call: Callable[[], dict[str, Any]], missing_codes: set[str]
) -> dict[str, Any] | None:
    try:
        return call()
    except ClientError as exc:
        if _error_code(exc) in missing_codes:
            return None
        raise


def inspect_bucket(client: Any, bucket: str, prefix: str) -> PreflightReport:
    """Inspect bucket-wide controls without reading object names or bytes."""
    if prefix.strip("/") != "nextpost":
        return PreflightReport(
            compatible=False,
            checks=(PreflightCheck("prefix", False, "must be exactly nextpost"),),
        )

    checks: list[PreflightCheck] = []
    try:
        client.head_bucket(Bucket=bucket)
        checks.append(PreflightCheck("bucket-access", True, "available"))

        public = client.get_public_access_block(Bucket=bucket)["PublicAccessBlockConfiguration"]
        public_safe = all(
            public.get(name) is True
            for name in (
                "BlockPublicAcls",
                "IgnorePublicAcls",
                "BlockPublicPolicy",
                "RestrictPublicBuckets",
            )
        )
        checks.append(
            PreflightCheck(
                "block-public-access",
                public_safe,
                "all controls enabled" if public_safe else "one or more controls disabled",
            )
        )

        policy_response = _optional_configuration(
            lambda: client.get_bucket_policy_status(Bucket=bucket),
            {"NoSuchBucketPolicy", "404"},
        )
        policy_status = policy_response.get("PolicyStatus", {}) if policy_response else None
        policy_safe = policy_status is None or policy_status.get("IsPublic") is False
        checks.append(
            PreflightCheck(
                "bucket-policy",
                policy_safe,
                (
                    "not configured"
                    if policy_status is None
                    else "not public"
                    if policy_safe
                    else "public or indeterminate"
                ),
            )
        )

        encryption = client.get_bucket_encryption(Bucket=bucket)
        rules = encryption.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
        checks.append(
            PreflightCheck(
                "default-encryption",
                bool(rules),
                "configured" if rules else "not configured",
            )
        )

        versioning = client.get_bucket_versioning(Bucket=bucket).get("Status", "Disabled")
        versioning_safe = versioning in {"Disabled", "Suspended", "Enabled"}
        checks.append(PreflightCheck("versioning", versioning_safe, str(versioning).lower()))

        object_lock = _optional_configuration(
            lambda: client.get_object_lock_configuration(Bucket=bucket),
            {"ObjectLockConfigurationNotFoundError", "NoSuchObjectLockConfiguration", "404"},
        )
        default_retention = bool(
            object_lock
            and object_lock.get("ObjectLockConfiguration", {})
            .get("Rule", {})
            .get("DefaultRetention")
        )
        checks.append(
            PreflightCheck(
                "object-lock-default-retention",
                not default_retention,
                "disabled" if not default_retention else "enabled and incompatible",
            )
        )

        lifecycle = _optional_configuration(
            lambda: client.get_bucket_lifecycle_configuration(Bucket=bucket),
            {"NoSuchLifecycleConfiguration", "404"},
        )
        lifecycle_count = len(lifecycle.get("Rules", [])) if lifecycle else 0
        checks.append(PreflightCheck("lifecycle-readable", True, f"{lifecycle_count} rule(s)"))

        replication = _optional_configuration(
            lambda: client.get_bucket_replication(Bucket=bucket),
            {"ReplicationConfigurationNotFoundError", "NoSuchReplicationConfiguration", "404"},
        )
        replicated = bool(
            replication and replication.get("ReplicationConfiguration", {}).get("Rules")
        )
        checks.append(
            PreflightCheck(
                "replication",
                not replicated,
                "disabled" if not replicated else "enabled and incompatible",
            )
        )

        client.list_object_versions(Bucket=bucket, Prefix="nextpost/", MaxKeys=1)
        checks.append(PreflightCheck("version-inventory-permission", True, "available"))
    except ClientError as exc:
        checks.append(
            PreflightCheck("owner-permissions", False, f"AWS denied check: {_error_code(exc)}")
        )
    except (KeyError, TypeError, ValueError):
        checks.append(PreflightCheck("response-shape", False, "unexpected AWS response"))

    return PreflightReport(
        compatible=bool(checks) and all(check.passed for check in checks),
        checks=tuple(checks),
    )


def main() -> None:
    region = os.getenv("S3_REGION", "").strip()
    bucket = os.getenv("S3_BUCKET", "").strip()
    prefix = os.getenv("S3_PREFIX", "nextpost").strip()
    if not region or not bucket:
        print(json.dumps({"compatible": False, "error": "missing S3_REGION or S3_BUCKET"}))
        raise SystemExit(2)
    client = boto3.client("s3", region_name=region)
    report = inspect_bucket(client, bucket, prefix)
    print(json.dumps(asdict(report), separators=(",", ":")))
    raise SystemExit(0 if report.compatible else 1)


if __name__ == "__main__":
    main()
