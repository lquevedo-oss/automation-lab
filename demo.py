from pathlib import Path
import json
from lab.workflows import *

root = Path(__file__).parent
fixtures = json.loads((root / "examples/synthetic.json").read_text(encoding="utf-8"))
findings = deduplicate_findings(fixtures["findings"])
revision = document_revision(fixtures["document_before"], fixtures["document_after"])
result = {
    "data_origin": "All examples are synthetic; no external systems were accessed.",
    "competitive_intelligence": {"findings": findings, "action": link_action({"title": "Revisar evidencia ficticia", "finding_id": findings[0]["id"]}, findings)},
    "engagement_funnel": funnel(fixtures["contacts"], fixtures["deals"]),
    "lost_opportunities": prioritize_lost_deals(fixtures["deals"]),
    "available_calendar_dates": suggest_dates(fixtures["bookings"], "2026-10-01", "CL"),
    "migration_audit": audit_migration(fixtures["source_rows"], fixtures["target_rows"]),
    "document_revision": revision,
    "slide_outline": slide_outline(fixtures["clients"]),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
