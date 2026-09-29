import copy
import json
from pathlib import Path
import unittest
from lab.workflows import *
from lab.invoice_validation import validate


class WorkflowTests(unittest.TestCase):
    def test_duplicate_evidence_ignores_tracking(self):
        rows = [{"title": " New feature ", "source": "https://example.com/news?utm_source=mail"}, {"title": "new FEATURE", "source": "https://example.com/news"}]
        self.assertEqual(len(deduplicate_findings(rows)), 1)

    def test_different_sources_remain_separate(self):
        rows = [{"title": "Feature", "source": "https://example.com/a"}, {"title": "Feature", "source": "https://example.com/b"}]
        self.assertEqual(len(deduplicate_findings(rows)), 2)

    def test_unknown_action_evidence_rejected(self):
        with self.assertRaises(ValueError):
            link_action({"title": "Task", "finding_id": "missing"}, [])

    def test_evidence_credentials_rejected(self):
        with self.assertRaises(ValueError):
            canonical_url("https://user:pass@localhost/a")

    def test_funnel_does_not_double_count_associated_deal(self):
        contacts = [{"id": "c1", "country": "CL", "downloaded": True}, {"id": "c2", "country": "CL", "downloaded": True}]
        deals = [{"id": "d1", "contact_ids": ["c1", "c2"], "stage": "won", "amount": "0.1"}, {"id": "d2", "contact_ids": ["c1"], "stage": "won", "amount": "0.2"}]
        row = funnel(contacts, deals)[0]
        self.assertEqual(row["associated_deals"], 2)
        self.assertEqual(row["associated_amount_demo"], "0.3")

    def test_unknown_loss_reason_requires_review(self):
        row = prioritize_lost_deals([{"id": "d1", "stage": "lost", "reason": "unclear", "amount": "5000"}])[0]
        self.assertTrue(row["needs_review"])
        self.assertFalse(row["recoverable"])

    def test_invalid_amount_rejected(self):
        with self.assertRaises(ValueError):
            prioritize_lost_deals([{"id": "d1", "stage": "lost", "reason": "timing", "amount": "NaN"}])

    def test_schedule_respects_country_capacity_and_weekends(self):
        bookings = [{"date": "2026-10-02", "country": "CL"}] * 2
        self.assertEqual(suggest_dates(bookings, "2026-10-01", "CL")[0], "2026-10-05")
        self.assertEqual(suggest_dates(bookings, "2026-10-01", "PE")[0], "2026-10-02")

    def test_migration_reports_duplicate_and_missing(self):
        result = audit_migration([{"id": "a"}, {"id": "a"}, {"id": "b"}], [{"id": "a"}])
        self.assertEqual(result["source_duplicates"], ["a"])
        self.assertEqual(result["missing"], ["b"])

    def test_revision_blocks_repeat_and_requires_review(self):
        current = {"title": "Demo", "body": "Second"}
        result = document_revision({"title": "Demo", "body": "First"}, current)
        self.assertEqual(result["changed_fields"], ["body"])
        self.assertTrue(document_revision(current, current, [result["sha256"]])["duplicate"])
        self.assertTrue(result["requires_human_review"])

    def test_document_escapes_supplied_html(self):
        output = render_document({"title": "<script>bad</script>", "body": "<b>text</b>"})
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)

    def test_invoice_fixture_validates_without_external_writes(self):
        fixture = json.loads((Path(__file__).parent.parent / "examples/invoice.json").read_text())
        self.assertTrue(validate(fixture)["valid"])

    def test_invoice_mismatched_total_rejected(self):
        fixture = json.loads((Path(__file__).parent.parent / "examples/invoice.json").read_text())
        fixture["document"]["invoice_total_clp"] += 1
        self.assertFalse(validate(fixture)["valid"])

    def test_nonfinite_invoice_quantity_rejected(self):
        fixture = json.loads((Path(__file__).parent.parent / "examples/invoice.json").read_text())
        fixture["lines"][0]["quantity_units"] = "NaN"
        self.assertFalse(validate(fixture)["valid"])


if __name__ == "__main__":
    unittest.main()
