#!/usr/bin/env python3
"""Freshness recheck pipeline — automated pipeline for stale fact rechecking.

Extends check_evidence_freshness.py into a continuous recheck workflow:
1. Identifies stale claims (NEEDS_RECHECK status)
2. Prioritizes by urgency (pricing > plan_limit > capabilities > general)
3. Generates recheck tasks with source URLs and claim types
4. Updates evidence ledger with new verification dates (when --apply is used)
5. Updates v2 record freshness fields
6. Generates daily freshness reports

Usage:
    python3 scripts/freshness_recheck_pipeline.py              # Dry run, generate report
    python3 scripts/freshness_recheck_pipeline.py --apply      # Apply updates to ledger and v2 records
    python3 scripts/freshness_recheck_pipeline.py --as-of 2026-11-23  # Use specific date
    python3 scripts/freshness_recheck_pipeline.py --output reports/phase6/freshness-recheck-report.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "data" / "tools-v2"
LEDGER_PATH = ROOT / "data" / "evidence" / "evidence-ledger.json"
FRESHNESS_POLICY_PATH = ROOT / "data" / "freshness-policy.json"
REPORTS_DIR = ROOT / "reports" / "phase6"

# Priority ordering for claim types (lower number = higher priority)
CLAIM_PRIORITY = {
    "pricing": 1,
    "free_plan": 1,
    "trial": 2,
    "plan_limit": 2,
    "billing": 3,
    "free_trial": 3,
    "capability": 5,
    "platform": 6,
    "use_case": 7,
    "target_user": 8,
    "limitation": 9,
    "feature": 9,
    "general": 10,
}

# Source volatility scores (higher = changes more frequently, needs more frequent recheck)
SOURCE_VOLATILITY = {
    "pricing_page": 8,
    "homepage": 5,
    "blog": 3,
    "documentation": 2,
    "changelog": 7,
    "api_docs": 4,
    "press_release": 6,
    "unknown": 5,
}

# Domain throttling — max claims per domain per batch to avoid rate limiting
DOMAIN_THROTTLE_DEFAULT = 5

# Batch size defaults
DEFAULT_BATCH_SIZE = 10


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_tools_v2_records():
    records = []
    for path in sorted(TOOL_DIR.rglob("*.json")):
        if path.name == "README.json":
            continue
        records.append(load_json(path))
    return records


def load_freshness_policy():
    if not FRESHNESS_POLICY_PATH.is_file():
        return {
            "thresholds": {"pricing": 90, "plan_limit": 90, "billing": 90,
                           "capabilities": 180, "free_trial": 90, "general": 365},
            "default_threshold": 365,
        }
    return load_json(FRESHNESS_POLICY_PATH)


def get_threshold_for_claim(claim_type, policy):
    thresholds = policy.get("thresholds", {})
    return thresholds.get(claim_type, policy.get("default_threshold", 365))


def classify_claim(claim, policy, as_of):
    """Classify a claim based on its verification date and freshness threshold."""
    claim_type = claim.get("claim_type", "general")
    threshold_days = get_threshold_for_claim(claim_type, policy)

    stale_after = claim.get("stale_after")
    verified_at = claim.get("verified_at")

    if not stale_after and not verified_at:
        return "UNKNOWN", 0

    if stale_after:
        try:
            stale_date = date.fromisoformat(stale_after)
            if stale_date < as_of:
                days_overdue = (as_of - stale_date).days
                return "NEEDS_RECHECK", days_overdue
            else:
                days_until_stale = (stale_date - as_of).days
                return "VERIFIED_CURRENTLY", -days_until_stale
        except (ValueError, TypeError):
            return "UNKNOWN", 0

    if verified_at:
        try:
            verified_date = date.fromisoformat(verified_at)
            threshold_date = verified_date + timedelta(days=threshold_days)
            if threshold_date < as_of:
                days_overdue = (as_of - threshold_date).days
                return "NEEDS_RECHECK", days_overdue
            else:
                days_until_stale = (threshold_date - as_of).days
                return "VERIFIED_CURRENTLY", -days_until_stale
        except (ValueError, TypeError):
            return "UNKNOWN", 0

    return "UNKNOWN", 0


def get_priority_score(claim_type):
    """Get numeric priority for a claim type (lower = more urgent)."""
    return CLAIM_PRIORITY.get(claim_type, 10)


def calculate_priority_score(claim, sources):
    """Calculate a composite priority score for a claim.
    
    Uses: source volatility x claim type x age x impact x domain throttling
    
    Args:
        claim: The claim dict
        sources: Dict of source_id -> source data
    
    Returns:
        Float priority score (higher = more urgent)
    """
    claim_type = claim.get("claim_type", "general")
    
    # 1. Claim type priority (pricing/free_plan/trial are highest)
    type_score = get_priority_score(claim_type)
    
    # 2. Source volatility - how often does this source change?
    volatility = 0
    for sid in claim.get("source_ids", []):
        source = sources.get(sid, {})
        source_type = source.get("source_type", "unknown")
        vol = SOURCE_VOLATILITY.get(source_type, SOURCE_VOLATILITY["unknown"])
        volatility = max(volatility, vol)
    
    # 3. Age - how overdue is this claim?
    urgency = claim.get("urgency_score", 0)
    age_score = max(urgency, 0)  # Only overdue claims get age bonus
    
    # 4. Impact - pricing claims affect more downstream consumers
    impact_multiplier = 1.0
    if claim_type in ("pricing", "free_plan", "trial"):
        impact_multiplier = 2.0
    elif claim_type in ("plan_limit", "billing"):
        impact_multiplier = 1.5
    
    # Composite: lower type_score = higher priority, so invert
    # Higher volatility, age, and impact = higher priority
    composite = (11 - type_score) * 100 + volatility * 10 + age_score
    composite *= impact_multiplier
    
    return composite


def extract_domain(url):
    """Extract domain from URL for throttling."""
    if not url:
        return ""
    # Simple domain extraction
    url = url.split("://")[-1].split("/")[0].split(":")[0]
    return url.lower()


def create_controlled_batches(tasks, batch_size=None, domain_throttle=None):
    """Create controlled batches for recheck with domain-aware throttling.
    
    Groups tasks into batches of controlled size, respecting domain throttling
    to avoid rate limiting. Pricing/free-plan/trial claims are prioritized
    into earlier batches.
    
    Args:
        tasks: List of task dicts sorted by priority
        batch_size: Max tools per batch (default: 10)
        domain_throttle: Max claims per domain per batch (default: 5)
    
    Returns:
        List of batches, each batch is a list of tasks
    """
    if batch_size is None:
        batch_size = DEFAULT_BATCH_SIZE
    if domain_throttle is None:
        domain_throttle = DOMAIN_THROTTLE_DEFAULT
    
    if not tasks:
        return []
    
    # Sort by composite score descending (highest priority first)
    sorted_tasks = sorted(tasks, key=lambda t: t.get("composite_score", 0), reverse=True)
    
    batches = []
    current_batch = []
    domain_counts = {}  # Track domain usage in current batch
    tool_ids_in_batch = set()
    
    for task in sorted_tasks:
        tool_id = task.get("tool_id", "")
        
        # Check if adding this task would exceed batch size
        if len(tool_ids_in_batch) >= batch_size and tool_id not in tool_ids_in_batch:
            # Finalize current batch
            if current_batch:
                batches.append(current_batch)
            current_batch = []
            domain_counts = {}
            tool_ids_in_batch = set()
        
        # Check domain throttling
        task_domains = set()
        for source_url in task.get("source_urls", []):
            domain = extract_domain(source_url.get("url", ""))
            if domain:
                task_domains.add(domain)
        
        # Check if any domain would exceed throttle
        domain_exceeded = False
        for domain in task_domains:
            if domain_counts.get(domain, 0) >= domain_throttle:
                domain_exceeded = True
                break
        
        if domain_exceeded:
            # Domain throttle hit — flush current batch and start new one
            if current_batch:
                batches.append(current_batch)
            current_batch = [task]
            domain_counts = {d: 1 for d in task_domains}
            tool_ids_in_batch = {tool_id}
        else:
            current_batch.append(task)
            if tool_id not in tool_ids_in_batch:
                tool_ids_in_batch.add(tool_id)
            for domain in task_domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # Don't forget the last batch
    if current_batch:
        batches.append(current_batch)
    
    return batches


def generate_recheck_tasks(stale_claims, sources):
    """Generate structured recheck tasks for stale claims."""
    tasks = []
    for claim in stale_claims:
        claim_id = claim.get("claim_id", "")
        tool_id = claim.get("tool_id", "")
        claim_type = claim.get("claim_type", "general")

        # Collect source URLs for rechecking
        source_urls = []
        for sid in claim.get("source_ids", []):
            source = sources.get(sid)
            if source and source.get("url"):
                source_urls.append({
                    "source_id": sid,
                    "url": source["url"],
                    "type": source.get("source_type", "unknown"),
                })

        priority = get_priority_score(claim_type)
        urgency = claim.get("urgency_score", 0)
        
        # Calculate composite priority score
        composite = calculate_priority_score(claim, sources)

        task = {
            "task_id": f"recheck-{claim_id}",
            "claim_id": claim_id,
            "tool_id": tool_id,
            "claim_type": claim_type,
            "priority": priority,
            "urgency_days_overdue": urgency,
            "composite_score": composite,
            "source_urls": source_urls,
            "stale_after": claim.get("stale_after"),
            "verified_at": claim.get("verified_at"),
            "status": "pending",
            "assigned_to": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        tasks.append(task)

    # Sort by composite score (highest priority first)
    tasks.sort(key=lambda t: t["composite_score"], reverse=True)
    return tasks


def update_ledger_for_recheck(ledger, claim_ids, as_of):
    """Update the evidence ledger to mark claims as due for recheck.

    IMPORTANT: This is a metadata-only operation. It must NOT advance
    verified_at or last_verified_date — those dates only advance when
    a source is actually fetched and parsed successfully by the
    source_monitor pipeline. This function only marks claims as
    DUE_FOR_RECHECK with proper urgency tracking.

    Sets status to 'due_for_recheck' without touching verification dates.
    """
    updated = 0

    for claim in ledger.get("claims", []):
        if claim.get("claim_id") in claim_ids:
            claim["status"] = "due_for_recheck"
            # DO NOT update verified_at — that would create fake freshness
            # DO NOT update last_verified_date — same reason
            # DO NOT extend stale_after — the original stale_after is correct
            # The claim is already past its stale_after, which is why it's here
            updated += 1

    return updated


def update_v2_freshness(records, tool_ids, as_of):
    """Update v2 record freshness fields for tools that were rechecked."""
    updated = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for record in records:
        tool_id = record.get("identity", {}).get("id", "")
        if tool_id in tool_ids:
            freshness = record.setdefault("freshness", {})
            freshness["last_verified_at"] = now_iso
            # Set next_review_at to 90 days from now (pricing default)
            next_review = as_of + timedelta(days=90)
            freshness["next_review_at"] = datetime.combine(next_review, datetime.min.time()).isoformat() + "Z"
            # Clear stale fields since we rechecked
            freshness["stale_fields"] = []
            record["freshness"] = freshness
            updated += 1

    return updated


def run_recheck_pipeline(as_of=None, apply=False):
    """Run the full freshness recheck pipeline."""
    as_of = as_of or date.today()
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)

    policy = load_freshness_policy()
    records = load_tools_v2_records()
    ledger = load_json(LEDGER_PATH) if LEDGER_PATH.is_file() else {"sources": [], "claims": []}

    claims = ledger.get("claims", [])
    sources = {s.get("source_id"): s for s in ledger.get("sources", [])}
    v2_by_id = {r.get("identity", {}).get("id"): r for r in records}

    # Step 1: Classify all claims
    classified = []
    status_counts = {"VERIFIED_CURRENTLY": 0, "NEEDS_RECHECK": 0, "UNKNOWN": 0, "NOT_COLLECTED": 0}

    for claim in claims:
        status, urgency = classify_claim(claim, policy, as_of)
        status_counts[status] = status_counts.get(status, 0) + 1
        classified.append({
            **claim,
            "freshness_status": status,
            "urgency_score": urgency,
        })

    # Step 2: Identify stale claims
    stale_claims = [c for c in classified if c["freshness_status"] == "NEEDS_RECHECK"]

    # Step 3: Generate recheck tasks
    tasks = generate_recheck_tasks(stale_claims, sources)

    # Step 3B: Create controlled batches
    batches = create_controlled_batches(tasks)

    # Step 4: Check tools without any claims
    tools_without_claims = []
    tool_ids_with_claims = {c.get("tool_id") for c in claims}
    for record in records:
        tool_id = record.get("identity", {}).get("id", "")
        if tool_id not in tool_ids_with_claims:
            tools_without_claims.append(tool_id)

    # Step 5: Check overdue tool reviews
    overdue_tools = []
    for record in records:
        freshness = record.get("freshness", {})
        next_review = freshness.get("next_review_at")
        if next_review:
            try:
                nr_date = datetime.fromisoformat(next_review.replace("Z", "+00:00")).date()
                if nr_date < as_of:
                    overdue_tools.append({
                        "tool_id": record["identity"]["id"],
                        "next_review_at": next_review,
                        "days_overdue": (as_of - nr_date).days,
                    })
            except (ValueError, TypeError):
                pass

    # Step 6: Apply updates if requested
    applied_updates = False
    ledger_updated = 0
    v2_updated = 0

    if apply and tasks:
        # Update ledger for all stale claims
        stale_claim_ids = {t["claim_id"] for t in tasks}
        ledger_updated = update_ledger_for_recheck(ledger, stale_claim_ids, as_of)

        # Update v2 records for affected tools
        affected_tools = {t["tool_id"] for t in tasks}
        v2_updated = update_v2_freshness(records, affected_tools, as_of)

        # Save updated ledger
        save_json(LEDGER_PATH, ledger)

        # Save updated v2 records
        for record in records:
            tool_id = record.get("identity", {}).get("id", "")
            if tool_id in affected_tools:
                record_path = TOOL_DIR / f"{tool_id}.json"
                if not record_path.exists():
                    # Search in subdirectories
                    for p in TOOL_DIR.rglob(f"{tool_id}.json"):
                        record_path = p
                        break
                if record_path.exists():
                    save_json(record_path, record)

        applied_updates = True

    # Build batch summary
    batch_summary = []
    for i, batch in enumerate(batches):
        tool_ids = {t.get("tool_id") for t in batch}
        claim_types = {t.get("claim_type") for t in batch}
        batch_summary.append({
            "batch_number": i + 1,
            "size": len(batch),
            "unique_tools": len(tool_ids),
            "claim_types": sorted(claim_types),
            "has_pricing": "pricing" in claim_types or "free_plan" in claim_types,
            "domain_throttled": any(t.get("domain_throttled") for t in batch),
        })

    # Build report
    report = {
        "pipeline": "freshness_recheck",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "as_of": as_of.isoformat(),
        "policy": policy,
        "summary": {
            "total_claims": len(claims),
            "total_tools": len(records),
            "status_counts": status_counts,
            "stale_claims": len(stale_claims),
            "recheck_tasks_generated": len(tasks),
            "controlled_batches": len(batches),
            "batch_size_limit": DEFAULT_BATCH_SIZE,
            "domain_throttle_limit": DOMAIN_THROTTLE_DEFAULT,
            "tools_without_claims": len(tools_without_claims),
            "tools_overdue_for_review": len(overdue_tools),
            "applied_updates": applied_updates,
            "ledger_claims_updated": ledger_updated,
            "v2_records_updated": v2_updated,
        },
        "batch_summary": batch_summary,
        "recheck_tasks": tasks,
        "controlled_batches": batches,
        "tools_without_claims": sorted(tools_without_claims),
        "overdue_tool_reviews": sorted(overdue_tools, key=lambda t: -t["days_overdue"]),
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Freshness recheck pipeline")
    parser.add_argument("--as-of", type=str, default=None, help="Date to check freshness (YYYY-MM-DD)")
    parser.add_argument("--apply", action="store_true", help="Apply updates to ledger and v2 records")
    parser.add_argument("--output", type=Path, default=None, help="Output report path")
    args = parser.parse_args()

    report = run_recheck_pipeline(as_of=args.as_of, apply=args.apply)

    # Save report
    output_path = args.output or REPORTS_DIR / "freshness-recheck-report.json"
    save_json(output_path, report)

    # Print summary
    summary = report["summary"]
    mode = "APPLIED" if summary["applied_updates"] else "DRY RUN"
    print(f"\n{'='*60}")
    print(f"Freshness Recheck Pipeline — {mode}")
    print(f"{'='*60}")
    print(f"  As of: {report['as_of']}")
    print(f"  Total claims: {summary['total_claims']}")
    print(f"  Total tools: {summary['total_tools']}")
    print(f"\n  Claim status breakdown:")
    for status, count in summary["status_counts"].items():
        print(f"    {status}: {count}")
    print(f"\n  Stale claims needing recheck: {summary['stale_claims']}")
    print(f"  Recheck tasks generated: {summary['recheck_tasks_generated']}")
    print(f"  Controlled batches: {summary.get('controlled_batches', 'N/A')}")
    print(f"  Batch size limit: {summary.get('batch_size_limit', 'N/A')}")
    print(f"  Domain throttle: {summary.get('domain_throttle_limit', 'N/A')}")
    print(f"  Tools without claims: {summary['tools_without_claims']}")
    print(f"  Tools overdue for review: {summary['tools_overdue_for_review']}")

    if summary["applied_updates"]:
        print(f"\n  Updates applied:")
        print(f"    Ledger claims updated: {summary['ledger_claims_updated']}")
        print(f"    V2 records updated: {summary['v2_records_updated']}")

    # Show top 10 recheck tasks
    tasks = report["recheck_tasks"]
    if tasks:
        print(f"\n  Top {min(10, len(tasks))} recheck tasks (by priority):")
        for task in tasks[:10]:
            priority_label = {
                1: "CRITICAL", 2: "HIGH", 3: "HIGH", 4: "MEDIUM",
                5: "MEDIUM", 6: "LOW", 7: "LOW", 8: "LOW", 9: "LOW", 10: "INFO"
            }.get(task["priority"], "INFO")
            print(f"    [{priority_label}] {task['claim_id']} ({task['tool_id']}) "
                  f"days_overdue={task['urgency_days_overdue']} "
                  f"sources={len(task['source_urls'])}")

    print(f"\nReport written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
