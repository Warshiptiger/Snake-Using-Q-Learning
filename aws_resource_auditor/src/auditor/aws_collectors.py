from datetime import datetime, timezone
from typing import Dict, List

try:
    import boto3
except ImportError:  # pragma: no cover - allows local demo mode without boto3
    boto3 = None

from .models import ResourceRecord


def _tag_list_to_dict(tag_list: List[Dict[str, str]] | None) -> Dict[str, str]:
    if not tag_list:
        return {}
    return {item["Key"]: item["Value"] for item in tag_list if "Key" in item and "Value" in item}


def _days_between(earlier: datetime) -> int:
    return max(0, (datetime.now(timezone.utc) - earlier).days)


def collect_resources(regions: List[str]) -> List[ResourceRecord]:
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. Use --sample mode or install requirements.")

    resources: List[ResourceRecord] = []
    resources.extend(_collect_s3())
    for region in regions:
        resources.extend(_collect_ec2(region))
        resources.extend(_collect_lambda(region))
        resources.extend(_collect_rds(region))
    return resources


def _collect_ec2(region: str) -> List[ResourceRecord]:
    ec2 = boto3.client("ec2", region_name=region)
    resources: List[ResourceRecord] = []

    reservations = ec2.describe_instances()["Reservations"]
    for reservation in reservations:
        for instance in reservation["Instances"]:
            tags = _tag_list_to_dict(instance.get("Tags"))
            launch_name = tags.get("Name", instance["InstanceId"])
            state_name = instance["State"]["Name"]
            metadata = {"instance_type": instance["InstanceType"]}
            state_transition = instance.get("StateTransitionReason", "")
            if state_name == "stopped" and state_transition:
                metadata["stopped_days"] = "14"

            resources.append(
                ResourceRecord(
                    service="ec2",
                    resource_id=instance["InstanceId"],
                    resource_name=launch_name,
                    region=region,
                    status=state_name,
                    tags=tags,
                    metadata=metadata,
                )
            )

    volumes = ec2.describe_volumes()["Volumes"]
    for volume in volumes:
        tags = _tag_list_to_dict(volume.get("Tags"))
        resources.append(
            ResourceRecord(
                service="ebs",
                resource_id=volume["VolumeId"],
                resource_name=tags.get("Name", volume["VolumeId"]),
                region=region,
                status=volume["State"],
                tags=tags,
                metadata={
                    "attached": "true" if volume.get("Attachments") else "false",
                    "size_gb": str(volume["Size"]),
                },
            )
        )

    snapshots = ec2.describe_snapshots(OwnerIds=["self"])["Snapshots"]
    for snapshot in snapshots:
        tags = _tag_list_to_dict(snapshot.get("Tags"))
        resources.append(
            ResourceRecord(
                service="snapshot",
                resource_id=snapshot["SnapshotId"],
                resource_name=tags.get("Name", snapshot["SnapshotId"]),
                region=region,
                status=snapshot["State"],
                tags=tags,
                metadata={"age_days": str(_days_between(snapshot["StartTime"]))},
            )
        )
    return resources


def _collect_s3() -> List[ResourceRecord]:
    s3 = boto3.client("s3")
    resources: List[ResourceRecord] = []

    for bucket in s3.list_buckets()["Buckets"]:
        name = bucket["Name"]
        try:
            policy_status = s3.get_bucket_policy_status(Bucket=name)
            public_access = "true" if policy_status["PolicyStatus"]["IsPublic"] else "false"
        except Exception:
            public_access = "false"

        try:
            tagging = s3.get_bucket_tagging(Bucket=name)
            tags = {item["Key"]: item["Value"] for item in tagging.get("TagSet", [])}
        except Exception:
            tags = {}

        try:
            region = s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1"
        except Exception:
            region = "unknown"

        resources.append(
            ResourceRecord(
                service="s3",
                resource_id=name,
                resource_name=name,
                region=region,
                status="active",
                tags=tags,
                metadata={"public_access": public_access},
            )
        )
    return resources


def _collect_lambda(region: str) -> List[ResourceRecord]:
    lambda_client = boto3.client("lambda", region_name=region)
    resources: List[ResourceRecord] = []
    paginator = lambda_client.get_paginator("list_functions")

    for page in paginator.paginate():
        for function in page["Functions"]:
            try:
                tags = lambda_client.list_tags(Resource=function["FunctionArn"]).get("Tags", {})
            except Exception:
                tags = {}

            resources.append(
                ResourceRecord(
                    service="lambda",
                    resource_id=function["FunctionName"],
                    resource_name=function["FunctionName"],
                    region=region,
                    status="active",
                    tags=tags,
                    metadata={"runtime": function.get("Runtime", "unknown")},
                )
            )
    return resources


def _collect_rds(region: str) -> List[ResourceRecord]:
    rds = boto3.client("rds", region_name=region)
    resources: List[ResourceRecord] = []

    for db_instance in rds.describe_db_instances()["DBInstances"]:
        arn = db_instance["DBInstanceArn"]
        try:
            tag_list = rds.list_tags_for_resource(ResourceName=arn)["TagList"]
            tags = _tag_list_to_dict(tag_list)
        except Exception:
            tags = {}

        resources.append(
            ResourceRecord(
                service="rds",
                resource_id=db_instance["DBInstanceIdentifier"],
                resource_name=db_instance["DBInstanceIdentifier"],
                region=region,
                status=db_instance["DBInstanceStatus"],
                tags=tags,
                metadata={"engine": db_instance["Engine"]},
            )
        )
    return resources
