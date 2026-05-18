import json
import os
from datetime import datetime, timezone

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None

from .aws_collectors import collect_resources
from .config import AuditConfig
from .evaluator import evaluate_resources


def _parse_list_env(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _build_config() -> AuditConfig:
    return AuditConfig(
        required_tags=_parse_list_env("REQUIRED_TAGS", "Owner,Environment,Project"),
        snapshot_age_days=int(os.getenv("SNAPSHOT_AGE_DAYS", "90")),
        stopped_instance_days=int(os.getenv("STOPPED_INSTANCE_DAYS", "14")),
        regions=_parse_list_env("AUDIT_REGIONS", "ap-south-1"),
    )


def _write_report_to_s3(bucket: str, payload: dict) -> str:
    if boto3 is None:
        raise RuntimeError("boto3 is required for Lambda execution.")

    s3 = boto3.client("s3")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    key = f"resource-audits/{timestamp}.json"
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json",
    )
    return key


def handler(event: dict, context: object) -> dict:
    config = _build_config()
    resources = collect_resources(config.regions)
    result = evaluate_resources(resources, config)
    payload = result.to_dict()
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()

    bucket = os.getenv("AUDIT_BUCKET")
    s3_key = None
    if bucket:
        s3_key = _write_report_to_s3(bucket, payload)

    return {
        "statusCode": 200,
        "resource_count": result.summary["resource_count"],
        "finding_count": result.summary["finding_count"],
        "findings_by_severity": result.summary["findings_by_severity"],
        "bucket": bucket,
        "key": s3_key,
    }
