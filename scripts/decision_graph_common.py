"""Shared validation helpers for the ToolNest Decision Graph v1 artifacts."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
SCHEMA_DIR = ROOT / "data" / "schemas"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
CHANGE_LEDGER_PATH = ROOT / "data" / "changes" / "tool-change-ledger.json"
LEGACY_DATA_PATH = ROOT / "data" / "tools.json"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

# Recognized claim status values for the evidence ledger
VALID_CLAIM_STATUSES = {
    "verified",
    "verified_official",
    "verified_official_dynamic",
    "editorial_assessment",
    "research_required",
    "official_source_unavailable",
    "official_source_conflict",
    "needs_review",
    "stale",
    "disputed",
}

# Field-level verification status vocabulary
VALID_VERIFICATION_STATUSES = {
    "verified_official",
    "verified_official_dynamic",
    "editorial_assessment",
    "research_required",
    "official_source_unavailable",
    "official_source_conflict",
    "do_not_publish",
}


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def is_url(value, *, allow_reference=False) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    if allow_reference and value.startswith("/"):
        return True
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_date(value) -> bool:
    if not isinstance(value, str) or not ISO_DATE_PATTERN.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_datetime(value) -> bool:
    if not isinstance(value, str) or not ISO_DATETIME_PATTERN.fullmatch(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def error(errors, message):
    errors.append(message)


def load_records():
    return [
        load_json(path)
        for path in sorted(TOOL_DIR.rglob("*.json"))
        if path.name != "README.json"
    ]


def load_legacy_ids():
    data = load_json(LEGACY_DATA_PATH)
    return {tool["id"] for tool in data.get("tools", []) if isinstance(tool, dict)}


def validate_schema_documents():
    errors = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        try:
            schema = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            error(errors, f"{path}: cannot parse schema: {exc}")
            continue
        for key in ("$schema", "$id", "title", "type"):
            if key not in schema:
                error(errors, f"{path}: missing schema metadata {key}")
        if schema.get("type") != "object":
            error(errors, f"{path}: root type must be object")
    return errors


def validate_ledger_shape(ledger=None):
    ledger = ledger if ledger is not None else load_json(LEDGER_PATH)
    errors = []
    if ledger.get("schema_version") != "evidence-ledger-v1":
        error(errors, "evidence ledger has the wrong schema_version")
    sources = ledger.get("sources", [])
    claims = ledger.get("claims", [])
    source_ids = [source.get("source_id") for source in sources]
    claim_ids = [claim.get("claim_id") for claim in claims]
    if len(source_ids) != len(set(source_ids)):
        error(errors, "evidence ledger contains duplicate source_id values")
    if len(claim_ids) != len(set(claim_ids)):
        error(errors, "evidence ledger contains duplicate claim_id values")
    source_map = {source.get("source_id"): source for source in sources}
    claim_map = {claim.get("claim_id"): claim for claim in claims}
    for source in sources:
        source_id = source.get("source_id", "<missing>")
        if not SLUG_PATTERN.fullmatch(source_id):
            error(errors, f"source {source_id} has an invalid source_id")
        if not is_url(source.get("url")):
            error(errors, f"source {source_id} has an invalid URL")
        if source.get("source_type") in {
            "official_pricing",
            "official_product",
            "official_documentation",
            "official_help",
            "official_legal",
        } and source.get("official") is not True:
            error(errors, f"source {source_id} must be official for its source_type")
        for field in ("accessed_at", "verified_at"):
            if not is_date(source.get(field)):
                error(errors, f"source {source_id} has an invalid {field}")
        currency = source.get("currency")
        if currency is not None and (
            not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency)
        ):
            error(errors, f"source {source_id} has an invalid currency")
    for claim in claims:
        claim_id = claim.get("claim_id", "<missing>")
        if not SLUG_PATTERN.fullmatch(claim_id):
            error(errors, f"claim {claim_id} has an invalid claim_id")
        if not SLUG_PATTERN.fullmatch(claim.get("tool_id", "")):
            error(errors, f"claim {claim_id} has an invalid tool_id")
        source_refs = claim.get("source_ids", [])
        if not source_refs:
            error(errors, f"claim {claim_id} has no evidence source")
        for source_id in source_refs:
            if source_id not in source_map:
                error(errors, f"claim {claim_id} references missing source {source_id}")
        for field in ("accessed_at", "verified_at", "stale_after"):
            if not is_date(claim.get(field)):
                error(errors, f"claim {claim_id} has an invalid {field}")
        currency = claim.get("currency")
        if currency is not None and (
            not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency)
        ):
            error(errors, f"claim {claim_id} has an invalid currency")
        status = claim.get("status")
        if status not in VALID_CLAIM_STATUSES:
            error(errors, f"claim {claim_id} has an invalid status: {status}")
        if status == "disputed" and not claim.get("disputed_by"):
            error(errors, f"disputed claim {claim_id} has no disputed_by value")
        verification_status = claim.get("verification_status")
        if verification_status is not None and verification_status not in VALID_VERIFICATION_STATUSES:
            error(errors, f"claim {claim_id} has an invalid verification_status: {verification_status}")
        replacement = claim.get("replacement_claim_id")
        if replacement is not None and replacement not in claim_map:
            error(errors, f"claim {claim_id} references missing replacement claim {replacement}")
    return errors


def validate_tool_records(records=None, ledger=None):
    records = records if records is not None else load_records()
    ledger = ledger if ledger is not None else load_json(LEDGER_PATH)
    errors = validate_ledger_shape(ledger)
    claims = {claim["claim_id"]: claim for claim in ledger.get("claims", [])}
    all_ids = {record.get("identity", {}).get("id") for record in records}
    all_ids |= load_legacy_ids()
    ids = []
    slugs = []
    for record in records:
        identity = record.get("identity", {})
        record_id = identity.get("id", "<missing>")
        ids.append(record_id)
        slugs.append(identity.get("slug"))
        if record.get("schema_version") != "toolnest-tool-v1":
            error(errors, f"record {record_id} has the wrong schema_version")
        for field in ("id", "slug"):
            if not SLUG_PATTERN.fullmatch(identity.get(field, "")):
                error(errors, f"record {record_id} has an invalid {field}")
        if not is_url(identity.get("official_url")):
            error(errors, f"record {record_id} has an invalid official_url")
        if identity.get("status") not in {
            "active",
            "limited",
            "discontinued",
            "acquired",
            "unknown",
        }:
            error(errors, f"record {record_id} has an invalid status")
        evidence = record.get("evidence", {})
        record_claim_refs = {
            ref.get("claim_id") for ref in evidence.get("claim_refs", [])
        }
        evidence_verification = evidence.get("verification_status")
        if evidence_verification is not None and evidence_verification not in VALID_VERIFICATION_STATUSES:
            error(errors, f"record {record_id} has an invalid evidence.verification_status: {evidence_verification}")
        for claim_id in record_claim_refs:
            claim = claims.get(claim_id)
            if claim is None:
                error(errors, f"record {record_id} references missing claim {claim_id}")
            elif claim.get("tool_id") != record_id:
                error(errors, f"claim {claim_id} belongs to a different tool")
        for source_id in evidence.get("source_ids", []):
            if source_id not in {source.get("source_id") for source in ledger.get("sources", [])}:
                error(errors, f"record {record_id} references missing source {source_id}")
        for claim in claims.values():
            if claim.get("tool_id") == record_id:
                if claim["claim_id"] not in record_claim_refs:
                    error(errors, f"record {record_id} omits claim {claim['claim_id']}")
                if claim.get("claim_type") in {"pricing", "plan_limit", "billing"}:
                    if not claim.get("source_ids") or not claim.get("billing_term"):
                        error(errors, f"pricing claim {claim['claim_id']} lacks source or billing context")
                    if not claim.get("currency"):
                        error(errors, f"pricing claim {claim['claim_id']} lacks currency context")
        publishing = record.get("publishing", {})
        tier = record.get("editorial", {}).get("editorial_tier")
        if tier not in {"A", "B", "C"}:
            error(errors, f"record {record_id} has an invalid editorial tier")
        if publishing.get("indexability") == "index" and not is_url(
            publishing.get("canonical_url")
        ):
            error(errors, f"record {record_id} is indexable without a canonical URL")
        if publishing.get("sitemap_eligible") and publishing.get("indexability") != "index":
            error(errors, f"record {record_id} is sitemap eligible but not indexable")
        if tier == "C" and (
            publishing.get("indexability") == "index"
            or publishing.get("sitemap_eligible") is True
        ):
            error(errors, f"Tier C record {record_id} cannot be indexable or sitemap eligible")
        freshness = record.get("freshness", {})
        for field in ("created_at", "updated_at", "last_verified_at", "next_review_at"):
            if freshness.get(field) is not None and not is_datetime(freshness.get(field)):
                error(errors, f"record {record_id} has an invalid freshness.{field}")
        for relation_field in (
            "alternatives",
            "related_tools",
            "compatible_tools",
            "replaces",
            "replaced_by",
        ):
            for item in record.get("relationships", {}).get(relation_field, []):
                # Handle both string IDs and structured alternative objects
                if isinstance(item, dict):
                    related_id = item.get("tool_id", "")
                    if not SLUG_PATTERN.fullmatch(related_id):
                        error(errors, f"record {record_id} has an invalid alternative tool_id: {related_id}")
                else:
                    related_id = item
                if related_id not in all_ids:
                    error(errors, f"record {record_id} references missing tool {related_id}")
    if len(ids) != len(set(ids)):
        error(errors, "decision graph contains duplicate tool IDs")
    if len(slugs) != len(set(slugs)):
        error(errors, "decision graph contains duplicate tool slugs")
    return errors


def validate_change_ledger():
    ledger = load_json(CHANGE_LEDGER_PATH)
    errors = []
    if ledger.get("schema_version") != "tool-change-ledger-v1":
        error(errors, "change ledger has the wrong schema_version")
    event_ids = []
    known_tools = {record["identity"]["id"] for record in load_records()} | load_legacy_ids()
    source_ids = {
        source["source_id"] for source in load_json(LEDGER_PATH).get("sources", [])
    }
    for event in ledger.get("events", []):
        event_ids.append(event.get("event_id"))
        if event.get("tool_id") not in known_tools:
            error(errors, f"change event references missing tool {event.get('tool_id')}")
        if not is_date(event.get("detected_at")):
            error(errors, f"change event {event.get('event_id')} has invalid detected_at")
        for source_id in event.get("source_ids", []):
            if source_id not in source_ids:
                error(errors, f"change event references missing source {source_id}")
    if len(event_ids) != len(set(event_ids)):
        error(errors, "change ledger contains duplicate event IDs")
    return errors


def validate_freshness(as_of=None, ledger=None, records=None):
    as_of = as_of or date.today()
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)
    ledger = ledger if ledger is not None else load_json(LEDGER_PATH)
    records = records if records is not None else load_records()
    errors = []
    for claim in ledger.get("claims", []):
        stale_after = date.fromisoformat(claim["stale_after"])
        if stale_after < as_of and claim.get("status") not in {
            "stale",
            "needs_review",
            "disputed",
            "official_source_unavailable",
            "official_source_conflict",
        }:
            error(
                errors,
                f"claim {claim['claim_id']} expired on {claim['stale_after']} without a stale status",
            )
    for record in records:
        freshness = record["freshness"]
        if freshness.get("next_review_at") is None:
            continue
        next_review = datetime.fromisoformat(
            freshness["next_review_at"].replace("Z", "+00:00")
        ).date()
        if next_review < as_of and not freshness.get("stale_fields"):
            error(
                errors,
                f"record {record['identity']['id']} is past next_review_at without stale_fields",
            )
    return errors


def validate_affiliate_separation(records=None):
    errors = []
    records = records if records is not None else load_records()
    for record in records:
        identity = record["identity"]
        monetization = record["monetization"]
        if monetization.get("official_non_affiliate_url") != identity.get("official_url"):
            error(
                errors,
                f"record {identity['id']} official_non_affiliate_url does not match official_url",
            )
        affiliate_url = monetization.get("affiliate_url")
        if affiliate_url is not None:
            if not is_url(affiliate_url):
                error(errors, f"record {identity['id']} has an invalid affiliate URL")
            if affiliate_url == identity.get("official_url"):
                error(errors, f"record {identity['id']} uses its official URL as affiliate URL")
        editorial_text = json.dumps(record.get("editorial", {})).lower()
        if "affiliate" in editorial_text or "commission" in editorial_text:
            error(errors, f"record {identity['id']} leaks affiliate language into editorial fields")
    return errors


def print_result(name, errors):
    if errors:
        print(f"{name}: FAIL")
        for message in errors:
            print(f"- {message}")
        return 1
    print(f"{name}: PASS")
    return 0
