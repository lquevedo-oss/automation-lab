"""Portable examples with synthetic fixtures and no external side effects.

These examples explain patterns used in business tooling. They do not contain
an employer's production rules, schemas, prompts, or infrastructure.
"""
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
from html import escape
import json
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def canonical_url(url):
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username:
        raise ValueError("Evidence must have a public HTTP URL without credentials")
    query = [(key, value) for key, value in parse_qsl(parts.query) if not key.lower().startswith("utm_")]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(sorted(query)), ""))


def deduplicate_findings(findings):
    """Retain the first observation and its evidence for each source/content."""
    seen, result = set(), []
    for finding in findings:
        evidence = canonical_url(finding["source"])
        normalized = " ".join(finding["title"].casefold().split())
        identity = sha256((evidence + "\n" + normalized).encode()).hexdigest()[:16]
        if identity not in seen:
            result.append({**finding, "id": identity, "source": evidence})
            seen.add(identity)
    return result


def link_action(action, findings):
    if action.get("finding_id") not in {item["id"] for item in findings}:
        raise ValueError("Action refers to unknown evidence")
    if not action.get("title", "").strip():
        raise ValueError("Action needs a title")
    return {**action, "status": "open"}


def funnel(contacts, deals):
    """Count associated engagement; these counts do not establish causality."""
    result = []
    countries = sorted({contact["country"] for contact in contacts})
    for country in countries:
        cohort = [contact for contact in contacts if contact["country"] == country]
        engaged = {contact["id"] for contact in cohort if contact.get("downloaded") or contact.get("demo_date")}
        associated = {deal["id"]: deal for deal in deals if engaged.intersection(deal.get("contact_ids", []))}
        won = [deal for deal in associated.values() if deal.get("stage") == "won"]
        amount = sum((Decimal(str(deal["amount"])) for deal in won), Decimal(0))
        result.append({"country": country, "engaged_contacts": len(engaged), "associated_deals": len(associated), "won_deals": len(won), "associated_amount_demo": str(amount)})
    return result


def prioritize_lost_deals(deals, *, minimum_amount=1000):
    """Demonstration policy only. Excludes unknown and nonrecoverable reasons."""
    output = []
    for deal in deals:
        if deal.get("stage") not in {"lost", "standby"}:
            continue
        recoverable = deal.get("reason") in {"timing", "feature_gap"}
        amount = Decimal(str(deal["amount"]))
        if not amount.is_finite() or amount < 0:
            raise ValueError("Amount must be finite and nonnegative")
        output.append({"id": deal["id"], "recoverable": recoverable, "priority": recoverable and amount >= minimum_amount, "needs_review": deal.get("reason") not in {"timing", "feature_gap", "price", "closed_business"}})
    return output


def suggest_dates(bookings, requested, country, *, capacity=2, limit=3):
    if capacity < 1 or limit < 1:
        raise ValueError("Capacity and limit must be positive")
    current = date.fromisoformat(requested)
    counts = Counter((item["date"], item["country"]) for item in bookings)
    suggestions = []
    for _ in range(366):
        current += timedelta(days=1)
        if current.weekday() < 5 and counts[(current.isoformat(), country)] < capacity:
            suggestions.append(current.isoformat())
        if len(suggestions) == limit:
            return suggestions
    raise ValueError("No capacity found within one year")


def audit_migration(source, target):
    """Expose duplicates and discrepancies instead of silently losing rows."""
    def index(rows):
        grouped = {}
        duplicates = []
        for row in rows:
            key = row["id"]
            if key in grouped:
                duplicates.append(key)
            grouped[key] = row
        return grouped, duplicates
    left, left_dupes = index(source)
    right, right_dupes = index(target)
    return {"source_duplicates": left_dupes, "target_duplicates": right_dupes, "missing": sorted(left.keys() - right.keys()), "unexpected": sorted(right.keys() - left.keys()), "changed": sorted(key for key in left.keys() & right.keys() if left[key] != right[key])}


def document_revision(previous, current, known_hashes=()):
    serialized = json.dumps(current, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = sha256(serialized.encode()).hexdigest()
    fields = sorted(previous.keys() | current.keys())
    return {"sha256": digest, "duplicate": digest in known_hashes, "changed_fields": [key for key in fields if previous.get(key) != current.get(key)], "requires_human_review": True}


def render_document(fields):
    """Editable HTML output, with all supplied text escaped."""
    title = escape(str(fields.get("title", "Documento Demo")))
    body = "".join(f"<section><h2>{escape(str(key))}</h2><p>{escape(str(value))}</p></section>" for key, value in fields.items() if key != "title")
    return f'<!doctype html><html lang="es"><meta charset="utf-8"><title>{title}</title><body><h1>{title}</h1>{body}</body></html>'


def slide_outline(clients, maximum=6):
    """Generic data-to-presentation outline; no real customer data."""
    ordered = sorted(clients, key=lambda row: (-row["size_demo"], row["name"]))[:maximum]
    return {"title": "Ejemplos ficticios", "cards": [{"title": row["name"], "subtitle": f'{row["size_demo"]} unidades de muestra', "features": sorted(set(row["features"]))} for row in ordered]}
