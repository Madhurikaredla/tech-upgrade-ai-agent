#!/usr/bin/env python3
"""
list-tasks.py

Scans docs/implementation/*/tasks.md and prints a flat task table.

Usage:
    python scripts/list-tasks.py [docs/implementation]
    python scripts/list-tasks.py [docs/implementation] --name "Alice"
    python scripts/list-tasks.py [docs/implementation] --sprint 2
    python scripts/list-tasks.py [docs/implementation] --module AUTH
    python scripts/list-tasks.py [docs/implementation] --open

Arguments:
    path        Root path to scan (default: docs/implementation)
    --name      Filter by Assigned to field (name match, case-insensitive)
    --sprint    Filter by sprint number
    --module    Filter by module name (e.g. AUTH)
    --open      Show only tasks not marked done in manifest (requires manifest)
    --manifest  Path to manifest.json (default: docs/.daksh/manifest.json)
"""

import sys
import re
import json
import argparse
from pathlib import Path


TASK_HEADER = re.compile(r"^#### (TASK-[A-Z]+-\d+): (.+)$")
FIELD = re.compile(r"^- \*\*(.+?):\*\* (.*)$")


def parse_tasks_file(path: Path) -> list[dict]:
    module = path.parent.name.upper()
    tasks = []
    current = None

    for line in path.read_text(encoding="utf-8").splitlines():
        m = TASK_HEADER.match(line)
        if m:
            if current:
                tasks.append(current)
            current = {
                "id": m.group(1),
                "summary": m.group(2).strip(),
                "module": module,
                "type": "",
                "sprint": "",
                "points": "",
                "assignee": "",
                "assigned_to": "",
                "depends_on": "",
                "status": "open",
            }
            continue

        if current:
            f = FIELD.match(line)
            if f:
                key, val = f.group(1).strip(), f.group(2).strip()
                if key == "Type":
                    current["type"] = val
                elif key == "Sprint":
                    current["sprint"] = val
                elif key == "Points":
                    current["points"] = val.split()[0]
                elif key == "Assignee":
                    current["assignee"] = val
                elif key == "Assigned to":
                    current["assigned_to"] = val
                elif key == "Depends on":
                    current["depends_on"] = val

    if current:
        tasks.append(current)

    return tasks


def load_task_statuses(manifest_path: Path) -> dict[str, str]:
    if not manifest_path.exists():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        statuses = {}
        for task_id, entry in data.get("traceability", {}).items():
            if isinstance(entry, dict):
                statuses[task_id] = entry.get("status", "not_started")
            elif isinstance(entry, str):
                statuses[task_id] = entry.lower()
        return statuses
    except (json.JSONDecodeError, AttributeError):
        return {}


def sprint_num(sprint_str: str) -> str:
    """Extract just the number from 'Sprint 2' or '2'."""
    m = re.search(r"\d+", sprint_str)
    return m.group(0) if m else sprint_str


def print_table(tasks: list[dict], name_mode: bool) -> None:
    if not tasks:
        print("No tasks found matching the given filters.")
        return

    if name_mode:
        headers = ["Task ID", "Module", "Summary", "Pts", "Sprint", "Role", "Assigned to", "Status"]
        rows = [
            [t["id"], t["module"], t["summary"][:50], t["points"],
             t["sprint"], t["assignee"], t["assigned_to"] or "—", t["status"]]
            for t in tasks
        ]
    else:
        headers = ["Task ID", "Module", "Summary", "Pts", "Sprint", "Role", "Depends on"]
        rows = [
            [t["id"], t["module"], t["summary"][:50], t["points"],
             t["sprint"], t["assignee"], t["depends_on"] or "none"]
            for t in tasks
        ]

    col_widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]

    def fmt_row(row):
        return "| " + " | ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(row)) + " |"

    print(fmt_row(headers))
    print("|-" + "-|-".join("-" * w for w in col_widths) + "-|")
    for row in rows:
        print(fmt_row(row))


def main():
    parser = argparse.ArgumentParser(description="List Daksh tasks across modules.")
    parser.add_argument("path", nargs="?", default="docs/implementation",
                        help="Root implementation directory (default: docs/implementation)")
    parser.add_argument("--name", help="Filter by Assigned to (case-insensitive)")
    parser.add_argument("--sprint", help="Filter by sprint number")
    parser.add_argument("--module", help="Filter by module name (e.g. AUTH)")
    parser.add_argument("--open", action="store_true", dest="open_only",
                        help="Show only open (not done) tasks")
    parser.add_argument("--manifest", default="docs/.daksh/manifest.json",
                        help="Path to manifest.json")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"Error: path '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    task_files = sorted(root.glob("*/tasks.md"))
    if not task_files:
        print("No tasks found. Run `/daksh tasks MODULE` first.", file=sys.stderr)
        sys.exit(1)

    task_statuses = load_task_statuses(Path(args.manifest))

    all_tasks = []
    skipped = []
    for f in task_files:
        try:
            all_tasks.extend(parse_tasks_file(f))
        except Exception as e:
            skipped.append((f, str(e)))

    for t in all_tasks:
        t["status"] = task_statuses.get(t["id"], "not_started")

    # Apply filters
    if args.module:
        all_tasks = [t for t in all_tasks if t["module"] == args.module.upper()]
    if args.sprint:
        all_tasks = [t for t in all_tasks if sprint_num(t["sprint"]) == args.sprint]
    if args.name:
        all_tasks = [
            t for t in all_tasks
            if t["assigned_to"].strip().lower() == args.name.strip().lower()
        ]
        if not all_tasks:
            print(f"No tasks found for Assigned to = '{args.name}'.")
            return
    if args.open_only:
        all_tasks = [t for t in all_tasks if t["status"] != "done"]

    name_mode = bool(args.name)
    print_table(all_tasks, name_mode)

    if skipped:
        print(f"\nWarning: skipped {len(skipped)} file(s) due to parse errors:")
        for f, err in skipped:
            print(f"  {f}: {err}")


if __name__ == "__main__":
    main()
