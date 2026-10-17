"""Read-only Elastic IP inventory analysis using synthetic AWS-style JSON."""
import argparse
import csv
import json
from pathlib import Path

FIELDS = ["account_alias", "region", "allocation_id", "public_ip", "association_id", "status", "monthly_estimate_usd", "recommendation"]
HOURS_PER_MONTH = 730
DEFAULT_HOURLY_RATE = 0.005  # illustrative public IPv4 hourly rate, not a live quote


def audit_addresses(records, hourly_rate=DEFAULT_HOURLY_RATE):
    """Return report rows; flag only unassociated addresses as review candidates."""
    if hourly_rate < 0:
        raise ValueError("hourly_rate must be nonnegative")
    rows = []
    for record in records:
        allocation_id = record.get("AllocationId")
        public_ip = record.get("PublicIp")
        if not allocation_id or not public_ip:
            raise ValueError("Each record needs AllocationId and PublicIp")
        association_id = record.get("AssociationId")
        unassociated = not bool(association_id)
        rows.append({
            "account_alias": record.get("AccountAlias", "demo"),
            "region": record.get("Region", "unknown"),
            "allocation_id": allocation_id,
            "public_ip": public_ip,
            "association_id": association_id or "",
            "status": "REVIEW_UNASSOCIATED" if unassociated else "ASSOCIATED",
            "monthly_estimate_usd": f"{HOURS_PER_MONTH * hourly_rate:.2f}" if unassociated else "0.00",
            "recommendation": "Verify ownership and dependencies before considering release" if unassociated else "No release recommendation",
        })
    return rows


def run(input_path, output_path, hourly_rate=DEFAULT_HOURLY_RATE):
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input must be a JSON array")
    rows = audit_addresses(payload, hourly_rate)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Audit synthetic AWS Elastic IP inventory")
    parser.add_argument("--input", default="sample_data/elastic_ips.json")
    parser.add_argument("--output", default="sample_reports/elastic_ip_audit.csv")
    parser.add_argument("--hourly-rate", type=float, default=DEFAULT_HOURLY_RATE)
    args = parser.parse_args()
    rows = run(args.input, args.output, args.hourly_rate)
    count = sum(row["status"] == "REVIEW_UNASSOCIATED" for row in rows)
    print(f"Audited {len(rows)} Elastic IPs; {count} unassociated review candidates. Report: {args.output}")


if __name__ == "__main__":
    main()
