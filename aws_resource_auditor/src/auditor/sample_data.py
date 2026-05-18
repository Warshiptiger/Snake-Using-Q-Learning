from typing import List

from .models import ResourceRecord


def load_sample_resources() -> List[ResourceRecord]:
    return [
        ResourceRecord(
            service="ec2",
            resource_id="i-0abc1234prod1",
            resource_name="payments-api-prod",
            region="ap-south-1",
            status="running",
            tags={"Owner": "platform-team", "Environment": "prod", "Project": "payments"},
            metadata={"instance_type": "t3.medium"},
        ),
        ResourceRecord(
            service="ec2",
            resource_id="i-0abc1234dev2",
            resource_name="inventory-dev",
            region="ap-south-1",
            status="stopped",
            tags={"Environment": "dev"},
            metadata={"instance_type": "t3.small", "stopped_days": "37"},
        ),
        ResourceRecord(
            service="ebs",
            resource_id="vol-0111222333",
            resource_name="orphaned-volume",
            region="ap-south-1",
            status="available",
            tags={"Project": "inventory"},
            metadata={"attached": "false", "size_gb": "100"},
        ),
        ResourceRecord(
            service="snapshot",
            resource_id="snap-0999888777",
            resource_name="legacy-snapshot",
            region="ap-south-1",
            status="completed",
            tags={"Owner": "data-team", "Environment": "prod"},
            metadata={"age_days": "143"},
        ),
        ResourceRecord(
            service="s3",
            resource_id="customer-assets-demo",
            resource_name="customer-assets-demo",
            region="ap-south-1",
            status="active",
            tags={"Owner": "marketing", "Project": "campaign-assets"},
            metadata={"public_access": "true"},
        ),
        ResourceRecord(
            service="lambda",
            resource_id="thumbnail-generator",
            resource_name="thumbnail-generator",
            region="ap-south-1",
            status="active",
            tags={"Owner": "media-team", "Environment": "prod", "Project": "assets"},
            metadata={"runtime": "python3.12"},
        ),
        ResourceRecord(
            service="rds",
            resource_id="orders-db-dev",
            resource_name="orders-db-dev",
            region="ap-south-1",
            status="available",
            tags={"Owner": "backend-team", "Environment": "dev", "Project": "orders"},
            metadata={"engine": "postgres"},
        ),
    ]
