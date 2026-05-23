#!/usr/bin/env python3
"""
jira-sync.py — bidirectional Jira sync for Daksh.

Usage:
  python scripts/jira-sync.py push [--module MODULE] [--dry-run] [--force]
  python scripts/jira-sync.py pull [--module MODULE] [--dry-run]
  python scripts/jira-sync.py status
  python scripts/jira-sync.py time-block start TASK-ID
  python scripts/jira-sync.py time-block stop TASK-ID
  python scripts/jira-sync.py transition TASK-ID STATUS-NAME
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_PATH = Path("docs/.daksh/manifest.json")
WORKFLOW_PATH = Path("docs/.daksh/jira-workflow.json")
IMPL_ROOT = Path("docs/implementation")


def load_workflow() -> dict:
    if not WORKFLOW_PATH.exists():
        sys.exit(f"ERROR: {WORKFLOW_PATH} not found. Run /daksh init to create it.")
    return json.loads(WORKFLOW_PATH.read_text())


# ── manifest ──────────────────────────────────────────────────────────────────

def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        sys.exit("ERROR: No Daksh pipeline found. Run /daksh init first.")
    return json.loads(MANIFEST_PATH.read_text())


def save_manifest(manifest: dict) -> None:
    tmp = MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    os.rename(tmp, MANIFEST_PATH)


# ── env + client ──────────────────────────────────────────────────────────────

def validate_env_vars() -> tuple[str, str, str]:
    for name in ("JIRA_SERVER", "JIRA_EMAIL", "JIRA_TOKEN"):
        if not os.environ.get(name):
            sys.exit(f"ERROR: {name} not set")
    server = os.environ["JIRA_SERVER"]
    if not server.startswith("https://"):
        sys.exit("ERROR: JIRA_SERVER must use HTTPS.")
    return server, os.environ["JIRA_EMAIL"], os.environ["JIRA_TOKEN"]


def validate_jira_manifest(manifest: dict) -> None:
    jira_cfg = manifest.get("jira", {})
    if not jira_cfg.get("project_key"):
        sys.exit("ERROR: manifest.jira.project_key not set. Edit manifest.json before push.")
    if not jira_cfg.get("board_id"):
        sys.exit("ERROR: manifest.jira.board_id not set. Edit manifest.json before push.")


def make_client():
    try:
        import jira as jiralib
    except ImportError:
        sys.exit("ERROR: jira library not installed. Run: uv pip install jira")
    server, email, token = validate_env_vars()
    try:
        return jiralib.JIRA(server=server, basic_auth=(email, token))
    except Exception as e:
        sys.exit(f"ERROR: Jira connection failed: {e}")


# ── tasks.md parsing ──────────────────────────────────────────────────────────

_TASK_HEADER = re.compile(r"^#### (TASK-[A-Z]+-\d+): (.+)$")
_FIELD = re.compile(r"^- \*\*(.+?):\*\* (.*)$")
_SECTION_HDR = re.compile(r"^- \*\*(.+?):\*\*\s*$")  # field header with no inline value


def parse_tasks_md(module: str) -> list[dict]:
    path = IMPL_ROOT / module / "tasks.md"
    if not path.exists():
        return []
    tasks, current, current_section = [], None, None
    for line in path.read_text().splitlines():
        m = _TASK_HEADER.match(line)
        if m:
            if current:
                tasks.append(current)
            current = {"id": m.group(1), "summary": m.group(2).strip(),
                       "module": module, "epic": "", "sprint": "", "assignee": "",
                       "type": "Story", "parent": None, "points": None,
                       "description": "", "acceptance_criteria": []}
            current_section = None
            continue
        if not current:
            continue
        # Multi-line section: indented sub-bullet
        if current_section == "ac" and re.match(r"^\s{2,}-\s", line):
            current["acceptance_criteria"].append(line.strip().lstrip("- ").strip())
            continue
        # Non-indented line ends multi-line section
        if current_section and not re.match(r"^\s{2,}", line):
            current_section = None
        f = _FIELD.match(line)
        if f:
            key, val = f.group(1).strip(), f.group(2).strip()
            if key == "Epic":
                current["epic"] = val
            elif key == "Sprint":
                current["sprint"] = val
            elif key == "Assigned to":
                current["assignee"] = val
            elif key == "Parent":
                current["parent"] = val or None
            elif key == "Type":
                current["type"] = val.split("/")[0].strip()
            elif key == "Points":
                try:
                    current["points"] = int(val.split()[0])
                except (ValueError, IndexError):
                    pass
            elif key == "Description":
                current["description"] = val
            elif key == "Acceptance criteria":
                current_section = "ac"
        else:
            s = _SECTION_HDR.match(line)
            if s and s.group(1).strip() == "Acceptance criteria":
                current_section = "ac"
    if current:
        tasks.append(current)
    return tasks


def update_tasks_md(module: str, task_or_updates, status: str | None = None) -> None:
    """Set Status column in the summary table.

    Supports both update_tasks_md(module, task_id, status) and
    update_tasks_md(module, {task_id: status, ...}).
    """
    path = IMPL_ROOT / module / "tasks.md"
    if not path.exists():
        return
    if isinstance(task_or_updates, dict):
        updates = task_or_updates
    else:
        if status is None:
            raise TypeError("status is required when updating a single task")
        updates = {task_or_updates: status}
    lines = path.read_text().splitlines()
    new_lines = []
    in_table = False
    status_col = None   # 0-based index; None = not determined yet
    need_sep_fix = False

    for line in lines:
        # Detect summary table header (starts with "| ID ")
        if not in_table and re.match(r"^\| ID ", line):
            in_table = True
            headers = [h.strip() for h in line.strip().strip("|").split("|")]
            if "Status" in headers:
                status_col = headers.index("Status")
                need_sep_fix = False
            else:
                status_col = len(headers)
                need_sep_fix = True
                line = line.rstrip() + " Status |"
            new_lines.append(line)
            continue

        # Separator row (only dashes and pipes)
        if in_table and re.match(r"^\|[-|]+\|$", line):
            if need_sep_fix:
                line = line.rstrip() + " ------ |"
                need_sep_fix = False
            new_lines.append(line)
            continue

        # Data row
        if in_table and re.match(r"^\| TASK-", line):
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            task_id = cols[0] if cols else ""
            new_status = updates.get(task_id, "")
            if status_col < len(cols):
                cols[status_col] = new_status
            else:
                while len(cols) < status_col:
                    cols.append("")
                cols.append(new_status)
            line = "| " + " | ".join(cols) + " |"
            new_lines.append(line)
            continue

        if in_table and line and not line.startswith("|"):
            in_table = False
        new_lines.append(line)

    path.write_text("\n".join(new_lines) + "\n")


# ── push ──────────────────────────────────────────────────────────────────────

def push(client, manifest: dict, module_filter: str | None, dry_run: bool, force: bool) -> None:
    jira_cfg = manifest.setdefault("jira", {})
    project_key = jira_cfg.get("project_key")

    modules = [m for m in manifest.get("modules", [])
               if not module_filter or m.upper() == module_filter.upper()]
    if not modules:
        sys.exit(f"ERROR: No modules matched {module_filter}.")
    ticket_map = jira_cfg.setdefault("ticket_map", {})

    # 1. Epics — one per module
    epic_map: dict[str, str | None] = {}
    for module in modules:
        epic_id = f"{module}_epic"
        legacy_epic_id = f"EPIC-{module}"
        existing_epic_key = ticket_map.get(epic_id) or ticket_map.get(legacy_epic_id)
        if existing_epic_key and legacy_epic_id in ticket_map and epic_id not in ticket_map:
            ticket_map[epic_id] = existing_epic_key
        if existing_epic_key and not force:
            epic_map[module] = existing_epic_key
            print(f"  Epic {module}: already synced ({existing_epic_key}) — skipped")
            continue
        print(f"  {'[DRY RUN] ' if dry_run else ''}Creating Epic: {module} Module")
        if dry_run:
            epic_map[module] = f"DRY-{module}"
            continue
        try:
            if force and existing_epic_key:
                client.issue(existing_epic_key).update(summary=f"{module} Module")
                epic_map[module] = existing_epic_key
                ticket_map[epic_id] = existing_epic_key
                print(f"    → updated {existing_epic_key}")
            else:
                epic = client.create_issue(project=project_key,
                                           issuetype={"name": "Epic"},
                                           summary=f"{module} Module")
                epic_map[module] = epic.key
                ticket_map[epic_id] = epic.key
                print(f"    → {epic.key}")
        except Exception as e:
            print(f"    WARNING: Epic creation failed for {module}: {e}", file=sys.stderr)
            epic_map[module] = None

    sprint_map: dict[str, str | int] = {}
    sprint_names = sorted(
        {task["sprint"] for module in modules for task in parse_tasks_md(module) if task.get("sprint")}
    )
    if sprint_names:
        print(f"  Resolving {len(sprint_names)} sprint(s)")
    if not dry_run and sprint_names:
        existing_sprints = {s.name: s.id for s in client.sprints(jira_cfg["board_id"])}
        sprint_map.update(existing_sprints)
    for sprint_name in sprint_names:
        if sprint_name in sprint_map:
            print(f"    Sprint {sprint_name}: already exists ({sprint_map[sprint_name]})")
            continue
        print(f"    {'[DRY RUN] ' if dry_run else ''}Creating Sprint: {sprint_name}")
        if dry_run:
            sprint_map[sprint_name] = f"DRY-{sprint_name}"
            continue
        sprint = client.create_sprint(sprint_name, jira_cfg["board_id"])
        sprint_map[sprint_name] = sprint.id
        print(f"      -> {sprint.id}")

    # 3. Stories — one per task
    # Sort: tasks with no parent first, then sub-tasks, so parent keys are in ticket_map before children need them
    raw_tasks = [(m, t) for m in modules for t in parse_tasks_md(m)]
    all_tasks = sorted(raw_tasks, key=lambda mt: 0 if not mt[1].get("parent") else 1)
    created = skipped = 0
    for module, task in all_tasks:
        task_id = task["id"]
        if task_id in ticket_map and not force:
            skipped += 1
            continue

        epic_key = epic_map.get(module)
        summary = f"[{task_id}] {task['summary']}"
        issue_type = task.get("type", "Story") or "Story"
        if issue_type not in ("Story", "Bug", "Task", "Sub-task", "Subtask", "Spike"):
            issue_type = "Story"
        if issue_type == "Subtask":
            issue_type = "Sub-task"
        if issue_type == "Spike":
            issue_type = "Story"  # Jira has no native Spike type; use Story
        points = task.get("points")

        desc_parts = []
        if task.get("description"):
            desc_parts.append(task["description"])
        if task.get("acceptance_criteria"):
            desc_parts.append("\nAcceptance Criteria:\n" +
                              "\n".join(f"[ ] {ac}" for ac in task["acceptance_criteria"]))
        description = "\n".join(desc_parts)

        print(f"  {'[DRY RUN] ' if dry_run else ''}Story {task_id} "
              f"[{issue_type}{f' {points}pt' if points else ''}]: {task['summary'][:50]}")

        if dry_run:
            created += 1
            continue

        try:
            if force and task_id in ticket_map:
                update = {"summary": summary}
                if description:
                    update["description"] = description
                if points:
                    update["customfield_10016"] = points
                try:
                    client.issue(ticket_map[task_id]).update(fields=update)
                except Exception as ue:
                    if "customfield_10016" in str(ue):
                        update.pop("customfield_10016", None)
                        client.issue(ticket_map[task_id]).update(fields=update)
                        print(f"    WARNING: Story points not set (field not on board screen)")
                    else:
                        raise
                sprint_id = sprint_map.get(task.get("sprint"))
                if sprint_id:
                    client.add_issues_to_sprint(sprint_id, [ticket_map[task_id]])
                print(f"    → updated {ticket_map[task_id]}")
                created += 1
                continue

            # Sub-tasks parent to their TASK parent ticket, not the Epic
            task_parent_id = task.get("parent")
            task_parent_key = ticket_map.get(task_parent_id) if task_parent_id else None
            parent_key = task_parent_key or epic_key

            fields: dict = {
                "project": project_key,
                "issuetype": {"name": issue_type},
                "summary": summary,
            }
            if description:
                fields["description"] = description
            if points:
                fields["customfield_10016"] = points
            if parent_key:
                fields["parent"] = {"key": parent_key}

            try:
                story = client.create_issue(**fields)
            except Exception as ce:
                if "customfield_10016" in str(ce):
                    fields.pop("customfield_10016", None)
                    print(f"    WARNING: Story points not set (field not on board screen)")
                    story = client.create_issue(**fields)
                else:
                    raise
            ticket_map[task_id] = story.key
            sprint_id = sprint_map.get(task.get("sprint"))
            if sprint_id:
                client.add_issues_to_sprint(sprint_id, [story.key])
            print(f"    → {story.key}")

            created += 1

        except Exception as e:
            print(f"    ERROR creating story {task_id}: {e}", file=sys.stderr)

    if skipped:
        print(f"\n  {skipped} task(s) already in ticket_map — skipped (--force to update)")
    print(f"\n  Push complete: {len(epic_map)} epic(s), {created} story(ies) in backlog.")

    if not dry_run:
        jira_cfg["synced_at"] = datetime.now(timezone.utc).isoformat()
        jira_cfg.setdefault("done_statuses", ["Done", "Closed", "Resolved"])
        save_manifest(manifest)

# ── pull ──────────────────────────────────────────────────────────────────────

def pull(client, manifest: dict, module_filter: str | None, dry_run: bool) -> None:
    jira_cfg = manifest.setdefault("jira", {})
    ticket_map = jira_cfg.get("ticket_map", {})
    done_statuses = set(jira_cfg.get("done_statuses") or ["Done", "Closed", "Resolved"])

    task_tickets = {k: v for k, v in ticket_map.items() if k.startswith("TASK-")}
    if module_filter:
        task_tickets = {k: v for k, v in task_tickets.items()
                        if k.startswith(f"TASK-{module_filter.upper()}-")}

    if not task_tickets:
        print("No task tickets in ticket_map. Run /daksh jira push first.")
        return

    traceability = manifest.setdefault("traceability", {})
    module_updates: dict[str, dict] = {}
    done_count = in_progress_count = 0

    for task_id, jira_key in task_tickets.items():
        try:
            issue = client.issue(jira_key, fields="status")
            status_name = issue.fields.status.name
        except Exception as e:
            print(f"  WARNING: Could not fetch {jira_key} ({task_id}): {e}", file=sys.stderr)
            continue

        is_done = status_name in done_statuses
        daksh_status = "done" if is_done else "in_progress"
        print(f"  {task_id} ({jira_key}): {status_name} → {daksh_status}")

        # Preserve time_blocks if present; upgrade flat string entries
        existing = traceability.get(task_id)
        if not isinstance(existing, dict):
            traceability[task_id] = {"status": daksh_status, "time_blocks": []}
        else:
            traceability[task_id]["status"] = daksh_status

        module = task_id.split("-")[1]
        module_updates.setdefault(module, {})[task_id] = "Done" if is_done else "in_progress"
        done_count += is_done
        in_progress_count += not is_done

    if not dry_run:
        for module, updates in module_updates.items():
            update_tasks_md(module, updates)
        manifest["jira"]["synced_at"] = datetime.now(timezone.utc).isoformat()
        save_manifest(manifest)

    print(f"\n  Pull complete: {done_count} done, {in_progress_count} in_progress.")


# ── time blocks ───────────────────────────────────────────────────────────────

def time_block_start(manifest: dict, task_id: str) -> None:
    traceability = manifest.setdefault("traceability", {})
    now = datetime.now(timezone.utc).isoformat()

    entry = traceability.get(task_id)
    if not isinstance(entry, dict):
        entry = {"status": "in_progress", "time_blocks": []}
    else:
        entry["status"] = "in_progress"

    # Auto-close any open block first
    for block in entry.get("time_blocks", []):
        if block["end"] is None:
            block["end"] = now
            print(f"  Auto-closed open block started at {block['start']}")
            traceability[task_id] = entry
            save_manifest(manifest)
            _submit_worklog(manifest, task_id, block)
            manifest = load_manifest()
            traceability = manifest["traceability"]
            entry = traceability[task_id]

    entry["time_blocks"].append({"start": now, "end": None, "jira_worklog_id": None})
    traceability[task_id] = entry
    save_manifest(manifest)
    print(f"  Time block started for {task_id} at {now}")


def time_block_stop(manifest: dict, task_id: str) -> None:
    traceability = manifest.get("traceability", {})
    entry = traceability.get(task_id)

    if not isinstance(entry, dict) or not entry.get("time_blocks"):
        sys.exit(f"ERROR: No traceability entry for {task_id}. Run /daksh impl {task_id} first.")

    open_block = next((b for b in entry["time_blocks"] if b["end"] is None), None)
    if not open_block:
        sys.exit(f"ERROR: No open time block for {task_id}.")

    open_block["end"] = datetime.now(timezone.utc).isoformat()
    save_manifest(manifest)
    print(f"  Time block closed for {task_id}")
    _submit_worklog(manifest, task_id, open_block)


def _submit_worklog(manifest: dict, task_id: str, block: dict) -> None:
    if block.get("jira_worklog_id"):
        return  # already submitted

    jira_key = manifest.get("jira", {}).get("ticket_map", {}).get(task_id)
    if not jira_key:
        print(f"  WARNING: {task_id} not in ticket_map — time block saved locally but not logged to Jira. Run /daksh jira push first.")
        return

    start = datetime.fromisoformat(block["start"])
    end = datetime.fromisoformat(block["end"])
    seconds = int((end - start).total_seconds())
    if seconds < 60:
        print(f"  Skipping worklog: duration < 1 minute")
        return

    hours, rem = divmod(seconds, 3600)
    time_spent = f"{hours}h {rem // 60}m" if hours else f"{rem // 60}m"

    try:
        client = make_client()
        worklog = client.add_worklog(jira_key, timeSpent=time_spent, started=start)
        block["jira_worklog_id"] = str(worklog.id)
        # Reload and save to get latest manifest state
        fresh = load_manifest()
        task_entry = fresh["traceability"].get(task_id, {})
        for b in task_entry.get("time_blocks", []):
            if b["start"] == block["start"] and b["end"] == block["end"]:
                b["jira_worklog_id"] = str(worklog.id)
                break
        save_manifest(fresh)
        print(f"  Worklog logged: {jira_key} — {time_spent} (id: {worklog.id})")
    except Exception as e:
        print(f"  WARNING: Worklog submission failed: {e}", file=sys.stderr)


# ── transition ────────────────────────────────────────────────────────────────

def _bfs_path(transitions_map: dict, from_status: str, to_status: str) -> list[str] | None:
    """BFS shortest path through workflow graph. Returns list of statuses including start and end."""
    if from_status == to_status:
        return [from_status]
    queue = [(from_status, [from_status])]
    visited = {from_status}
    while queue:
        current, path = queue.pop(0)
        for nxt in transitions_map.get(current, []):
            if nxt == to_status:
                return path + [nxt]
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, path + [nxt]))
    return None


def _transition_aliases(target: str) -> list[str]:
    aliases = {
        "Open": ["Open Item", "open"],
        "Development in Progress": ["Task In Progress"],
        "Dev Internal Review": ["Development Review"],
        "Done": ["Work Done", "done"],
    }
    return [target, *aliases.get(target, [])]


def transition(client, manifest: dict, task_id: str, status_name: str) -> None:
    jira_key = manifest.get("jira", {}).get("ticket_map", {}).get(task_id)
    if not jira_key:
        sys.exit(f"ERROR: {task_id} not in ticket_map. Run /daksh jira push first.")

    workflow = load_workflow()
    issue = client.issue(jira_key, fields="status,issuetype")
    current_status = issue.fields.status.name
    issue_type = issue.fields.issuetype.name
    graph_key = "bug" if issue_type == "Bug" else "story"
    transitions_map = workflow.get(graph_key, {}).get("transitions", {})

    path = _bfs_path(transitions_map, current_status, status_name)
    if path is None:
        sys.exit(f"ERROR: No path from '{current_status}' to '{status_name}' in {graph_key} workflow.")

    for target in path[1:]:  # skip current status
        available = client.transitions(jira_key)
        candidates = {name.lower() for name in _transition_aliases(target)}
        match = next((t for t in available if t["name"].lower() in candidates), None)
        if not match:
            names = [t["name"] for t in available]
            sys.exit(f"ERROR: Jira won't accept '{target}' from current state. Available: {names}")
        client.transition_issue(jira_key, match["id"])
        print(f"  {jira_key}: {current_status} → {target}")
        current_status = target


# ── status ────────────────────────────────────────────────────────────────────

def status_cmd(manifest: dict) -> None:
    jira_cfg = manifest.get("jira", {})
    ticket_map = jira_cfg.get("ticket_map", {})

    if not ticket_map:
        print("No tickets in ticket_map. Run /daksh jira push first.")
        return

    traceability = manifest.get("traceability", {})
    done_count = sum(1 for v in traceability.values() if isinstance(v, dict) and v.get("status") == "done")
    open_blocks = sum(
        1
        for v in traceability.values()
        if isinstance(v, dict)
        for b in v.get("time_blocks", [])
        if b.get("end") is None
    )
    print(f"  Last sync:        {jira_cfg.get('synced_at') or 'Never synced'}")
    print(f"  Ticket count:     {len(ticket_map)}")
    print(f"  Done tasks:       {done_count}")
    print(f"  Open time blocks: {open_blocks}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(prog="jira-sync.py")
    sub = parser.add_subparsers(dest="cmd")

    p_push = sub.add_parser("push")
    p_push.add_argument("--module")
    p_push.add_argument("--dry-run", action="store_true")
    p_push.add_argument("--force", action="store_true")

    p_pull = sub.add_parser("pull")
    p_pull.add_argument("--module")
    p_pull.add_argument("--dry-run", action="store_true")

    sub.add_parser("status")

    p_tb = sub.add_parser("time-block")
    p_tb.add_argument("action", choices=["start", "stop"])
    p_tb.add_argument("task_id")

    p_tr = sub.add_parser("transition")
    p_tr.add_argument("task_id")
    p_tr.add_argument("status_name")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)

    manifest = load_manifest()

    if args.cmd == "status":
        status_cmd(manifest)
        return

    if args.cmd == "time-block":
        if args.action == "start":
            time_block_start(manifest, args.task_id)
        else:
            time_block_stop(manifest, args.task_id)
        return

    if args.cmd == "transition":
        validate_env_vars()
        transition(make_client(), manifest, args.task_id, args.status_name)
        return

    if args.cmd == "push":
        validate_jira_manifest(manifest)
        if args.dry_run:
            push(None, manifest, args.module, True, args.force)
            return
        validate_env_vars()
        push(make_client(), manifest, args.module, False, args.force)
    elif args.cmd == "pull":
        validate_jira_manifest(manifest)
        if args.dry_run:
            pull(None, manifest, args.module, True)
            return
        validate_env_vars()
        pull(make_client(), manifest, args.module, False)


if __name__ == "__main__":
    main()
