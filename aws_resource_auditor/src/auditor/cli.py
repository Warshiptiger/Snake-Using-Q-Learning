import argparse
from pathlib import Path

from .aws_collectors import collect_resources
from .config import AuditConfig
from .evaluator import evaluate_resources
from .report_writer import write_reports
from .sample_data import load_sample_resources


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit AWS resources for tagging, exposure, and governance issues."
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run using built-in sample data instead of live AWS resources.",
    )
    parser.add_argument(
        "--regions",
        nargs="+",
        default=["ap-south-1"],
        help="AWS regions to scan when not using sample mode.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[2] / "reports"),
        help="Directory for report output files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AuditConfig(regions=args.regions)

    if args.sample:
        resources = load_sample_resources()
    else:
        resources = collect_resources(config.regions)

    result = evaluate_resources(resources, config)
    output_dir = Path(args.output_dir)
    write_reports(result, output_dir)

    print(f"Resources scanned: {result.summary['resource_count']}")
    print(f"Findings: {result.summary['finding_count']}")
    print(f"Report written to: {output_dir}")


if __name__ == "__main__":
    main()
