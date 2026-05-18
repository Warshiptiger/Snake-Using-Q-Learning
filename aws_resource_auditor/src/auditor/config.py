from dataclasses import dataclass, field
from typing import List


@dataclass
class AuditConfig:
    required_tags: List[str] = field(
        default_factory=lambda: ["Owner", "Environment", "Project"]
    )
    snapshot_age_days: int = 90
    stopped_instance_days: int = 14
    regions: List[str] = field(default_factory=lambda: ["ap-south-1"])
