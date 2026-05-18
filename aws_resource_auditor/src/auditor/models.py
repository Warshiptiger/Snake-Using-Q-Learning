from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass
class ResourceRecord:
    service: str
    resource_id: str
    resource_name: str
    region: str
    status: str
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class Finding:
    severity: str
    category: str
    service: str
    resource_id: str
    region: str
    message: str
    recommendation: str
    owner: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class AuditResult:
    resources: List[ResourceRecord]
    findings: List[Finding]
    summary: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "summary": self.summary,
            "resources": [resource.to_dict() for resource in self.resources],
            "findings": [finding.to_dict() for finding in self.findings],
        }
