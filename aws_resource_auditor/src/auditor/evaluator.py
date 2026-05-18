from collections import Counter, defaultdict
from typing import Dict, List

from .config import AuditConfig
from .models import AuditResult, Finding, ResourceRecord


def _owner_of(resource: ResourceRecord) -> str:
    return resource.tags.get("Owner", "unassigned")


def evaluate_resources(resources: List[ResourceRecord], config: AuditConfig) -> AuditResult:
    findings: List[Finding] = []
    service_counter: Counter[str] = Counter()
    region_counter: Counter[str] = Counter()
    severity_counter: Counter[str] = Counter()
    resources_by_owner: Dict[str, int] = defaultdict(int)

    for resource in resources:
        service_counter[resource.service] += 1
        region_counter[resource.region] += 1
        resources_by_owner[_owner_of(resource)] += 1

        missing_tags = [tag for tag in config.required_tags if not resource.tags.get(tag)]
        if missing_tags:
            findings.append(
                Finding(
                    severity="medium",
                    category="tagging",
                    service=resource.service,
                    resource_id=resource.resource_id,
                    region=resource.region,
                    message=f"Missing required tags: {', '.join(missing_tags)}",
                    recommendation="Add the missing ownership and environment tags.",
                    owner=_owner_of(resource),
                )
            )

        if resource.service == "s3" and resource.metadata.get("public_access") == "true":
            findings.append(
                Finding(
                    severity="high",
                    category="public_access",
                    service=resource.service,
                    resource_id=resource.resource_id,
                    region=resource.region,
                    message="S3 bucket appears to allow public access.",
                    recommendation="Review the bucket policy and block public access unless explicitly required.",
                    owner=_owner_of(resource),
                )
            )

        if resource.service == "ebs" and resource.metadata.get("attached") == "false":
            findings.append(
                Finding(
                    severity="medium",
                    category="unused_resource",
                    service=resource.service,
                    resource_id=resource.resource_id,
                    region=resource.region,
                    message="EBS volume is unattached.",
                    recommendation="Review whether the volume is still needed and remove or archive it if not.",
                    owner=_owner_of(resource),
                )
            )

        if resource.service == "snapshot":
            age_days = int(resource.metadata.get("age_days", "0"))
            if age_days >= config.snapshot_age_days:
                findings.append(
                    Finding(
                        severity="low",
                        category="stale_backup",
                        service=resource.service,
                        resource_id=resource.resource_id,
                        region=resource.region,
                        message=f"Snapshot is {age_days} days old.",
                        recommendation="Confirm retention requirements and clean up stale snapshots where appropriate.",
                        owner=_owner_of(resource),
                    )
                )

        if resource.service == "ec2" and resource.status == "stopped":
            stopped_days = int(resource.metadata.get("stopped_days", "0"))
            if stopped_days >= config.stopped_instance_days:
                findings.append(
                    Finding(
                        severity="medium",
                        category="idle_compute",
                        service=resource.service,
                        resource_id=resource.resource_id,
                        region=resource.region,
                        message=f"EC2 instance has been stopped for {stopped_days} days.",
                        recommendation="Check whether the instance should be terminated, resized, or restarted.",
                        owner=_owner_of(resource),
                    )
                )

    for finding in findings:
        severity_counter[finding.severity] += 1

    summary = {
        "resource_count": len(resources),
        "finding_count": len(findings),
        "services": dict(service_counter),
        "regions": dict(region_counter),
        "findings_by_severity": dict(severity_counter),
        "resources_by_owner": dict(resources_by_owner),
        "required_tags": config.required_tags,
    }
    return AuditResult(resources=resources, findings=findings, summary=summary)
