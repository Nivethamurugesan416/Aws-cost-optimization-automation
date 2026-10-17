import csv
import json
import tempfile
import unittest
from pathlib import Path
from src.elastic_ip_audit import audit_addresses, run


class ElasticIPAuditTests(unittest.TestCase):
    def test_unassociated_is_flagged(self):
        rows = audit_addresses([{"AllocationId":"eipalloc-x", "PublicIp":"192.0.2.1"}])
        self.assertEqual(rows[0]["status"], "REVIEW_UNASSOCIATED")
        self.assertEqual(rows[0]["monthly_estimate_usd"], "3.65")

    def test_associated_is_not_flagged(self):
        rows = audit_addresses([{"AllocationId":"eipalloc-x", "PublicIp":"192.0.2.1", "AssociationId":"eipassoc-x"}])
        self.assertEqual(rows[0]["status"], "ASSOCIATED")
        self.assertEqual(rows[0]["monthly_estimate_usd"], "0.00")

    def test_missing_required_field(self):
        with self.assertRaises(ValueError):
            audit_addresses([{"AllocationId":"eipalloc-x"}])

    def test_negative_rate_rejected(self):
        with self.assertRaises(ValueError):
            audit_addresses([], hourly_rate=-1)

    def test_end_to_end_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "input.json"
            target = Path(temp) / "output.csv"
            source.write_text(json.dumps([{"AllocationId":"eipalloc-x", "PublicIp":"192.0.2.1"}]))
            run(source, target)
            with target.open(newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "REVIEW_UNASSOCIATED")


if __name__ == "__main__":
    unittest.main()
