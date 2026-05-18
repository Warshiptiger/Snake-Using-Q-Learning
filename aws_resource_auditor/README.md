# AWS Resource Auditor and Governance Reporter

This project scans AWS resources and produces a governance report focused on ownership, tagging hygiene, public exposure, and obvious infrastructure waste signals.

It was designed as a practical cloud operations project rather than a billing-only tool. The same output can still support FinOps conversations because it improves visibility into resource ownership, tagging compliance, and potentially wasteful infrastructure.

## What it checks

- missing required tags
- public S3 buckets
- unattached EBS volumes
- old EBS snapshots
- stopped EC2 instances
- region-wise inventory counts

## Supported services

- EC2 instances
- EBS volumes
- EBS snapshots
- S3 buckets
- Lambda functions
- RDS instances

## Project structure

```text
aws_resource_auditor/
  README.md
  requirements.txt
  template.yaml
  src/
    auditor/
      __init__.py
      lambda_handler.py
      cli.py
      config.py
      evaluator.py
      report_writer.py
      sample_data.py
      aws_collectors.py
      models.py
  reports/
```

## Run locally with sample data

This works without AWS credentials and is useful for demos or GitHub screenshots.

```bash
python -m aws_resource_auditor.src.auditor.cli --sample
```

## Run against AWS

If your environment has AWS credentials configured and `boto3` installed:

```bash
python -m aws_resource_auditor.src.auditor.cli --regions ap-south-1 us-east-1
```

## Run as a Lambda

The project also includes a Lambda handler so it can be scheduled through EventBridge.

- handler: `src.auditor.lambda_handler.handler`
- output: JSON report written to S3, with a compact summary returned in the invocation response
- trigger: EventBridge schedule such as daily or weekly scans

Expected Lambda environment variables:

- `AUDIT_REGIONS`
- `AUDIT_BUCKET`
- `SNAPSHOT_AGE_DAYS`
- `STOPPED_INSTANCE_DAYS`
- `REQUIRED_TAGS`

Example values:

```text
AUDIT_REGIONS=ap-south-1,us-east-1
AUDIT_BUCKET=my-audit-output-bucket
SNAPSHOT_AGE_DAYS=90
STOPPED_INSTANCE_DAYS=14
REQUIRED_TAGS=Owner,Environment,Project
```

## Deploy with AWS SAM

Build:

```bash
sam build
```

Deploy:

```bash
sam deploy --guided
```

The included `template.yaml` creates:

- a Lambda function
- an S3 bucket for report output
- an EventBridge scheduled rule
- an IAM role policy with read-only inventory permissions for the scanned services
- permission for the Lambda function to write reports to the output bucket

## Output

Each run writes two files into `reports/`:

- `resource_audit_report.json`
- `resource_audit_summary.txt`

## Why this project is useful

- improves cloud visibility
- enforces ownership and tagging hygiene
- helps surface obvious waste
- supports engineering, platform, and governance teams
- can be extended into scheduled automation with Lambda and EventBridge

## Future improvements

- email summary via SES or SNS
- store historical runs in S3
- add DynamoDB for trend tracking
- integrate AWS Config findings
- score teams on compliance trends
