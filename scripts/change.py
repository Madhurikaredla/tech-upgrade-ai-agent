#!/usr/bin/env python3
"""
daksh change — mechanical CR state management.

Handles the stateful parts of /daksh change: allocate CR-NNN, scaffold
the CR document, mark touched stages as pending_approval, allocate a
change task ID, and update the manifest.  The LLM is responsible for
content authoring (change summary, doc patches) before and after this
script runs.

Usage:
  python scripts/change.py --module AUTH \
      --title "Fix auth flow to use OAuth2" \
      --raised-by "Yeshwanth" \
      --touched-docs "docs/implementation/AUTH/trd.md,docs/implementation/AUTH/prd.md" \
      [--tier trd] [--affected-tasks "TASK-AUTH-001,TASK-AUTH-003"]
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

MANIFEST_PATH = Path("docs/.daksh/manifest.json")
IMPL_ROOT = Path("docs/implementation")

DOC_TIER_MAP = {
    "tasks.md": "tasks",
    "trd.md":   "trd",
    "prd.md":   "prd",
    "brd.md":   "brd",
    "roadmap.md": "roadmap",
}

TIER_RANK = {"tasks": 0, "trd": 1, "prd": 2, "brd": 3, "roadmap": 4}


# ── helpers ──────────────────────────────────────────────────────────────────

def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        sys.exit("ERROR: No Daksh pipeline found. Run /daksh init first.")
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: Invalid manifest JSON: {exc}")


def git_commit(files: list[Path], message: str) -> None:
    try:
        subprocess.run(["git", "add", "--"] + [str(f) for f in files],
                       check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nWARNING: git commit failed: {e}", file=sys.stderr)


def infer_tier(touched_docs: list[str]) -> str | None:
    """Infer the safest (highest) tier from touched doc basenames."""
    highest: str | None = None
    for doc in touched_docs:
        basename = Path(doc).name
        tier = DOC_TIER_MAP.get(basename)
        if tier and (highest is None or TIER_RANK[tier] > TIER_RANK.get(highest, -1)):
            highest = tier
    return highest


def next_cr_id(change_records: dict) -> str:
    """Allocate the next CR-NNN, zero-padded to 3 digits."""
    existing = [k for k in change_records if re.match(r"^CR-\d{3}$", k)]
    if not existing:
        return "CR-001"
    highest = max(int(k.split("-")[1]) for k in existing)
    return f"CR-{highest + 1:03d}"


def next_task_id(module: str, traceability: dict) -> str:
    """Allocate the next TASK-{MODULE}-NNN from the traceability map."""
    pattern = re.compile(rf"^TASK-{re.escape(module)}-(\d{{3}})$")
    nums = [int(m.group(1)) for k in traceability if (m := pattern.match(k))]
    nxt = (max(nums) + 1) if nums else 1
    return f"TASK-{module}-{nxt:03d}"


def find_stage_for_doc(stages: dict, doc_path: str) -> tuple[str, dict] | None:
    for key, data in stages.items():
        output = data.get("output")
        paths = output if isinstance(output, list) else [output] if output else []
        if doc_path in paths:
            return key, data
    return None


CR_TEMPLATE = """\
# {cr_id} — {title}

**Date:** {today}
**Tasks affected:** {affected_tasks}
**Raised by:** {raised_by}
**Tier:** {tier}

## What was specified
[To be filled by the LLM — quote or describe the original spec]

## What reality showed
[To be filled by the LLM — what was found during implementation]

## Impact
[To be filled by the LLM — what breaks or changes if we proceed as specced]

## Proposed resolution
[To be filled by the LLM — what the engineer proposes]

## Change Summary
[To be filled by the LLM — section-by-section diff summary, produced before any doc is patched]

## Decision
[Filled in by TL/PTL via /daksh approve {cr_id}]

## Status: OPEN
"""


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a change record and update manifest state.")
    parser.add_argument("--module", required=True,
                        help="Module short name (e.g. AUTH)")
    parser.add_argument("--title", required=True,
                        help="One-line CR description")
    parser.add_argument("--raised-by", required=True,
                        help="Name of the person raising the CR")
    parser.add_argument("--touched-docs", required=True,
                        help="Comma-separated list of doc paths this CR will modify")
    parser.add_argument("--tier", default=None,
                        help="Override tier (tasks|trd|prd|brd|roadmap). "
                             "If omitted, inferred from touched docs.")
    parser.add_argument("--affected-tasks", default=None,
                        help="Comma-separated TASK-IDs affected, or omit for 'inferred'")
    args = parser.parse_args()

    module = args.module.upper()
    manifest = load_manifest()

    # Validate module
    if module not in [m.upper() for m in manifest.get("modules", [])]:
        sys.exit(f"ERROR: Module '{module}' not found in manifest.modules.")

    touched_docs = [p.strip() for p in args.touched_docs.split(",") if p.strip()]
    if not touched_docs:
        sys.exit("ERROR: --touched-docs must list at least one document path.")

    # Validate touched docs exist on disk
    for doc in touched_docs:
        if not Path(doc).exists():
            sys.exit(f"ERROR: Touched document not found: {doc}")

    # Resolve tier
    tier = args.tier
    if tier:
        if tier not in TIER_RANK:
            sys.exit(f"ERROR: Invalid tier '{tier}'. "
                     f"Must be one of: {', '.join(TIER_RANK)}.")
    else:
        tier = infer_tier(touched_docs)
        if not tier:
            sys.exit("ERROR: Cannot infer tier from touched docs. "
                     "Pass --tier explicitly.")
        print(f"  Tier inferred from touched docs: {tier}")

    change_records = manifest.setdefault("change_records", {})
    stages = manifest.get("stages", {})
    traceability = manifest.setdefault("traceability", {})

    # ── overlap check ────────────────────────────────────────────────────
    for cr_id, cr in change_records.items():
        if cr.get("status") != "OPEN":
            continue
        overlap = set(touched_docs) & set(cr.get("touched_docs", []))
        if overlap:
            print(f"WARNING: {cr_id} already touches: {', '.join(sorted(overlap))}")
            print(f"  Consider resolving {cr_id} before raising a new CR.\n")

    # ── allocate IDs ─────────────────────────────────────────────────────
    cr_id = next_cr_id(change_records)
    change_task_id = next_task_id(module, traceability)
    today = date.today().isoformat()

    affected_tasks = args.affected_tasks or f"inferred: see ## Change Summary"

    # ── scaffold CR document ─────────────────────────────────────────────
    cr_dir = IMPL_ROOT / module / "change-records"
    cr_dir.mkdir(parents=True, exist_ok=True)
    cr_path = cr_dir / f"{cr_id}.md"

    cr_content = CR_TEMPLATE.format(
        cr_id=cr_id,
        title=args.title,
        today=today,
        affected_tasks=affected_tasks,
        raised_by=args.raised_by,
        tier=tier,
    )
    cr_path.write_text(cr_content)

    # ── mark touched stages as pending_approval ──────────────────────────
    marked_stages: list[str] = []
    for doc in touched_docs:
        match = find_stage_for_doc(stages, doc)
        if not match:
            print(f"  WARNING: {doc} not mapped to any stage — skipping stage mark")
            continue
        stage_key, stage_data = match
        if stage_key not in marked_stages:
            stage_data["status"] = "pending_approval"
            marked_stages.append(stage_key)

    # ── update manifest ──────────────────────────────────────────────────
    change_records[cr_id] = {
        "module": module,
        "path": str(cr_path),
        "status": "OPEN",
        "raised_by": args.raised_by,
        "date": today,
        "tier": tier,
        "touched_docs": touched_docs,
        "change_task": change_task_id,
        "change_summary": args.title,
        "approvals": [],
    }

    traceability[change_task_id] = {
        "parent": cr_id,
        "children": [],
        "stage": "50",
        "module": module,
        "status": "todo",
    }

    # ── append skeleton task to tasks.md ────────────────────────────────
    tasks_path = IMPL_ROOT / module / "tasks.md"
    if tasks_path.exists():
        task_skeleton = (
            f"\n\n#### {change_task_id}: [{cr_id}] {args.title}\n"
            f"- **Depends on:** none\n"
            f"- **Decision budget:** 30 min\n"
            f"- **Status:** todo\n"
            f"\n"
            f"**Acceptance criteria:**\n"
            f"- [ ] All changes listed in {cr_id} ## Change Summary are applied\n"
            f"- [ ] {cr_id} approved via `/daksh approve {cr_id}`\n"
            f"- [ ] Patched docs pass `/daksh preflight`\n"
        )
        with tasks_path.open("a") as f:
            f.write(task_skeleton)
    else:
        print(f"  WARNING: {tasks_path} not found — change task not written to disk")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    # ── git commit scaffolding ───────────────────────────────────────────
    commit_files = [cr_path, MANIFEST_PATH]
    if tasks_path.exists():
        commit_files.append(tasks_path)
    git_commit(
        commit_files,
        f"chore(daksh): raise {cr_id} — {args.title}",
    )

    # ── report ───────────────────────────────────────────────────────────
    print(f"\n  Change record scaffolded:")
    print(f"    CR:          {cr_id}")
    print(f"    Tier:        {tier}")
    print(f"    Document:    {cr_path}")
    print(f"    Change task: {change_task_id}")
    print(f"    Stages marked pending_approval: {', '.join(marked_stages) or 'none'}")
    print(f"\n  Next steps (LLM):")
    print(f"    1. Fill in the CR sections (What was specified, What reality showed, etc.)")
    print(f"    2. Write the ## Change Summary (before patching any doc)")
    print(f"    3. Apply doc patches listed in the summary")
    print(f"    4. Refine {change_task_id} in tasks.md if needed (skeleton already written)")
    print(f"    5. Commit doc changes")
    print(f"    6. Tell user: run `/daksh approve {cr_id}`")


if __name__ == "__main__":
    main()
