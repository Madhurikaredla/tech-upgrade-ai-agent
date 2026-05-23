#!/usr/bin/env python3
"""discovery.py — scaffold a Discovery Record (DR-NNN) for a legacy constraint.

Usage:
    python scripts/discovery.py --module AUTH --title "Legacy session tokens in localStorage"
    python scripts/discovery.py --module AUTH --title "..." --task TASK-AUTH-003 --raised-by Priya

Unlike Change Records (CR-NNN), Discovery Records do not reference a Daksh spec.
They reference existing code. Use a CR when spec and reality diverge; use a DR
when you find a constraint in existing code with no spec to diverge from.
"""
import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

MANIFEST_PATH = Path("docs/.daksh/manifest.json")


def next_dr_number(change_records_dir: Path) -> int:
    existing = [
        int(p.stem.split("-")[1])
        for p in change_records_dir.glob("DR-*.md")
        if p.stem.split("-")[1].isdigit()
    ]
    return max(existing, default=0) + 1


def git_user_name() -> str:
    result = subprocess.run(
        ["git", "config", "user.name"], capture_output=True, text=True
    )
    return result.stdout.strip() or "Unknown"


DR_TEMPLATE = """\
# {dr_id} — {title}

**Module:** {module}
**Task:** {task}
**Raised by:** {raised_by}
**Date:** {date}
**Status:** OPEN

## What we found

<!-- Describe the constraint: what exists, how it works, why it's a constraint -->

## Where it lives

<!-- File paths, module names, service boundaries — concrete pointers into the codebase -->

## Impact on current work

<!-- How this constrains {task}: what you can't do, what you have to do differently -->

## Impact on baseline

<!-- Does docs/baseline.md or the module baseline need to be updated? -->

## Proposed path forward

<!-- Options + recommended approach. Advisory — no approval required to proceed -->

## Decision

<!-- Filled in by TL/PTL -->

## Status: OPEN
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True, metavar="MODULE")
    parser.add_argument("--title", required=True)
    parser.add_argument("--task", default="TBD")
    parser.add_argument("--raised-by", default=None, dest="raised_by")
    args = parser.parse_args()

    module = args.module.upper()
    raised_by = args.raised_by or git_user_name()

    if not MANIFEST_PATH.exists():
        sys.exit("ERROR: No Daksh pipeline found. Run /daksh init first.")
    manifest = json.loads(MANIFEST_PATH.read_text())

    cr_dir = Path(f"docs/implementation/{module}/change-records")
    if not cr_dir.exists():
        sys.exit(f"ERROR: {cr_dir} does not exist. Run /daksh init for module {module} first.")

    n = next_dr_number(cr_dir)
    dr_id = f"DR-{n:03d}"
    dr_path = cr_dir / f"{dr_id}.md"

    dr_path.write_text(DR_TEMPLATE.format(
        dr_id=dr_id,
        title=args.title,
        module=module,
        task=args.task,
        raised_by=raised_by,
        date=date.today().isoformat(),
    ))

    manifest.setdefault("change_records", {})[dr_id] = {
        "type": "discovery",
        "module": module,
        "title": args.title,
        "status": "OPEN",
        "raised_by": raised_by,
        "raised_at": date.today().isoformat(),
        "task_ref": args.task,
        "path": str(dr_path),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    print(f"{dr_id} created: {dr_path}")
    print(f"  Module:    {module}")
    print(f"  Task:      {args.task}")
    print(f"  Raised by: {raised_by}")
    print(f"\nRun `/daksh risk-profile` to see all open discovery records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
