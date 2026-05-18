import json
from datetime import datetime, timezone
from pathlib import Path

from .models import AuditResult


def write_reports(result: AuditResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "resource_audit_report.json"
    summary_path = output_dir / "resource_audit_summary.txt"

    payload = result.to_dict()
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "AWS Resource Auditor Summary",
        "",
        f"Resources scanned: {result.summary['resource_count']}",
        f"Findings: {result.summary['finding_count']}",
        "",
        "Findings by severity:",
    ]
    for severity, count in result.summary["findings_by_severity"].items():
        lines.append(f"- {severity}: {count}")

    lines.extend(["", "Top findings:"])
    if result.findings:
        for finding in result.findings[:10]:
            lines.append(
                f"- [{finding.severity.upper()}] {finding.service} {finding.resource_id}: {finding.message}"
            )
    else:
        lines.append("- No findings")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
