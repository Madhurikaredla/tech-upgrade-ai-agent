#!/usr/bin/env python3
"""
daksh approve — gate approval and revision flagging.

Usage:
  python scripts/approve.py <stage> [MODULE] --approver <name> [--revise --reason <text>]

Examples:
  python scripts/approve.py brd --approver Yeshwanth
  python scripts/approve.py prd AUTH --approver Yeshwanth
  python scripts/approve.py brd --approver Yeshwanth --revise --reason "FR-004 scope too broad"
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

MANIFEST_PATH = Path("docs/.daksh/manifest.json")

# Stage codes per `daksh` command. Module-scoped stages use ":{}" templates.
# 40-band stages (40a..40d) are per-module selectable and mergeable; merges are
# read from manifest.modules[MODULE].stages_merged rather than encoded here.
STAGE_MAP = {
    "onboard":  "00",
    "vision":   "10",
    "brd":      "20",
    "roadmap":  "30",
    "prd":      "40a:{}",
    "solution": "40b:{}",
    "trd":      "40c:{}",
    "tasks":    "40d:{}",
    "impl":     "50:{}",
}

# PTL can approve anything; TL can approve roadmap and all module-band stages.
ROLE_PERMISSIONS = {
    "PTL": {"*"},
    "TL":  {"30", "40a", "40b", "40c", "40d", "50"},
}

# Tiered approval authority for change records based on highest doc touched
CR_TIER_ROLES = {
    "tasks":   {"PTL", "TL"},
    "trd":     {"PTL", "TL"},
    "prd":     {"PTL"},
    "brd":     {"PTL", "Client"},
    "roadmap": {"PTL", "Client"},
}

CR_ID_RE = re.compile(r"^CR-\d{3}$")

# Maps doc basenames to tier names for fail-safe inference
DOC_TIER_MAP = {
    "tasks.md": "tasks",
    "trd.md":   "trd",
    "prd.md":   "prd",
    "brd.md":   "brd",
    "roadmap.md": "roadmap",
}

TIER_RANK = {"tasks": 0, "trd": 1, "prd": 2, "brd": 3, "roadmap": 4}


def infer_tier(touched_docs: list[str]) -> str | None:
    """Infer the safest (highest) tier from touched doc basenames."""
    highest: str | None = None
    for doc in touched_docs:
        basename = Path(doc).name
        tier = DOC_TIER_MAP.get(basename)
        if tier and (highest is None or TIER_RANK[tier] > TIER_RANK.get(highest, -1)):
            highest = tier
    return highest


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit(files: list[Path], message: str) -> None:
    try:
        subprocess.run(["git", "add", "--"] + [str(f) for f in files], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nWARNING: git commit failed: {e}", file=sys.stderr)


def merge_group_for(manifest: dict, module: str, stage_prefix: str) -> list[str] | None:
    """Return the merged-stage group (sorted) this stage belongs to for the given
    module, or None if it stands alone. Reads manifest.module_config[MODULE].stages_merged.
    """
    mod_config = manifest.get("module_config", {})
    mod_entry = mod_config.get(module.upper(), {})
    for group in mod_entry.get("stages_merged", []):
        if stage_prefix in group:
            return sorted(group)
    return None


def resolve_key(stage: str, module: str | None, manifest: dict) -> str:
    template = STAGE_MAP.get(stage)
    if not template:
        sys.exit(f"ERROR: Unknown stage '{stage}'.")
    if "{}" not in template:
        return template
    if not module:
        sys.exit(f"ERROR: Stage '{stage}' requires a MODULE argument.")
    prefix, _, _ = template.partition(":")
    module_uc = module.upper()
    group = merge_group_for(manifest, module_uc, prefix)
    if group:
        return f"{'+'.join(group)}:{module_uc}"
    return template.format(module_uc)


def count_open_questions(doc_path: Path) -> int:
    text = doc_path.read_text()
    in_section = False
    count = 0
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+Open [Qq]uestions", line):
            in_section = True
            continue
        if in_section and re.match(r"^#{1,3}\s", line):
            break
        if in_section and re.match(r"^\d+\.", line):
            count += 1
    return count


def role_can_approve(role: str, key: str, manifest: dict | None = None) -> bool:
    # Manifest-configured authority takes precedence over hardcoded map.
    if manifest:
        stage_authority = (
            manifest.get("org", {}).get("governance", {}).get("stage_authority", {})
        )
        # Normalize: "40a+40c:AUTH" -> first stage in merge group as the
        # authority key. Stage authority is per individual stage, so any
        # merged-stage approval is gated by the strictest member: we require
        # the role to be authorized for *all* stages in the group.
        prefix = key.split(":")[0]
        members = prefix.split("+")
        if any(m in stage_authority for m in members):
            return all(
                role in stage_authority[m]
                for m in members if m in stage_authority
            )
    allowed = ROLE_PERMISSIONS.get(role, set())
    if "*" in allowed:
        return True
    prefix = key.split(":")[0]
    # Merged stages: role must be authorized for every stage in the group.
    members = prefix.split("+")
    return all(m in allowed for m in members)


def cr_required_roles(tier: str) -> list[set[str]]:
    """Return the distinct role slots that must each be filled to approve a CR.

    For most tiers one approver suffices.  For brd/roadmap the design requires
    both a PTL *and* a Client sign-off — two separate slots.
    """
    if tier in ("brd", "roadmap"):
        return [{"PTL"}, {"Client"}]
    return [CR_TIER_ROLES.get(tier, {"PTL"})]


def find_stage_for_doc(stages: dict, doc_path: str) -> tuple[str, dict] | None:
    """Return (stage_key, stage_data) that owns *doc_path*, or None."""
    for key, data in stages.items():
        output = data.get("output")
        paths = output if isinstance(output, list) else [output] if output else []
        if doc_path in paths:
            return key, data
    return None


def approve_cr(manifest: dict, cr_id: str, approver: str) -> None:
    """Record one approval on a CR.  Resolve the CR only when all required
    role slots are filled (respects approvals_per_gate and multi-role tiers).
    """
    change_records = manifest.get("change_records", {})
    if cr_id not in change_records:
        sys.exit(f"ERROR: {cr_id} not found in manifest.change_records.")
    cr = change_records[cr_id]

    if cr.get("status") == "RESOLVED":
        sys.exit(f"ERROR: {cr_id} is already RESOLVED.")

    # --- roster & authority ---
    roster = {m["name"]: m["role"] for m in manifest.get("team_roster", [])}
    if approver not in roster:
        sys.exit(f"ERROR: '{approver}' is not in the team roster.")
    role = roster[approver]

    # --- resolve tier (fail-safe: infer upward, block if unknown) ---
    tier = cr.get("tier")
    if not tier:
        inferred = infer_tier(cr.get("touched_docs", []))
        if inferred:
            tier = inferred
            print(f"WARNING: {cr_id} has no 'tier' field. "
                  f"Inferred '{tier}' from touched docs (safest plausible).")
        else:
            sys.exit(f"ERROR: {cr_id} has no 'tier' field and it cannot be "
                     f"inferred from touched_docs. Add 'tier' to the CR in "
                     f"manifest.change_records before approving.")

    slots = cr_required_roles(tier)
    tier_roles = CR_TIER_ROLES.get(tier, {"PTL"})  # roles with authority for this tier
    prior_approvals = cr.get("approvals", [])
    prior_roles = {a["role"] for a in prior_approvals}

    # Phase 1: can the approver fill an unfilled authority slot?
    can_fill = any(role in slot and not (slot & prior_roles) for slot in slots)
    # PTL wildcard: can fill any unfilled slot regardless of tier listing
    if not can_fill and "*" in ROLE_PERMISSIONS.get(role, set()):
        can_fill = any(not (slot & prior_roles) for slot in slots)

    # Phase 2: all authority slots filled but count not met — accept
    # count-filling approvals from the SAME tier-scoped roles only.
    if not can_fill:
        all_slots_filled = all(slot & prior_roles for slot in slots)
        required = manifest.get("rules", {}).get("approvals_per_gate", 1)
        count_not_met = len(prior_approvals) < required
        if all_slots_filled and count_not_met and role in tier_roles:
            can_fill = True

    if not can_fill:
        already = ", ".join(sorted(prior_roles)) or "none"
        needed = " + ".join("/".join(sorted(s)) for s in slots)
        sys.exit(f"ERROR: {cr_id} (tier: {tier}) needs [{needed}]. "
                 f"Already have: [{already}]. Role '{role}' cannot fill a "
                 f"remaining slot or add a count-filling approval.")

    # Duplicate-approver guard
    if any(a["by"] == approver for a in prior_approvals):
        sys.exit(f"ERROR: '{approver}' has already approved {cr_id}.")

    # --- validate paths ---
    cr_path = Path(cr["path"])
    if not cr_path.exists():
        sys.exit(f"ERROR: CR document not found: {cr_path}")
    touched = [Path(p) for p in cr.get("touched_docs", [])]
    for p in touched:
        if not p.exists():
            sys.exit(f"ERROR: Touched document not found: {p}")

    # --- overlap warning ---
    for other_id, other_cr in change_records.items():
        if other_id == cr_id or other_cr.get("status") != "OPEN":
            continue
        overlap = set(cr.get("touched_docs", [])) & set(other_cr.get("touched_docs", []))
        if overlap:
            print(f"WARNING: {other_id} also touches: {', '.join(sorted(overlap))}")
            print(f"  Consider approving or resolving {other_id} first.\n")

    today = date.today().isoformat()
    all_paths = [cr_path] + touched

    # --- append approval block to all docs (preserving prior blocks) ---
    approval_block = (
        f"\nApproved by: {approver}\n"
        f"Role:        {role}\n"
        f"Date:        {today}\n"
        f"Via:         {cr_id}\n"
    )
    for p in all_paths:
        text = p.read_text()
        # Append to existing Approval section, never overwrite
        if "## Approval" in text:
            p.write_text(text.rstrip() + "\n" + approval_block)
        else:
            p.write_text(text.rstrip() + "\n\n## Approval\n" + approval_block)

    # --- record approval in manifest ---
    approval_entry = {"by": approver, "role": role, "date": today}
    cr.setdefault("approvals", []).append(approval_entry)

    # --- check if all slots are now filled ---
    filled_roles = {a["role"] for a in cr["approvals"]}
    all_filled = all(slot & filled_roles for slot in slots)
    required = manifest.get("rules", {}).get("approvals_per_gate", 1)
    enough_count = len(cr["approvals"]) >= required

    if all_filled and enough_count:
        # Resolve: flip CR status, update doc text
        cr_text = cr_path.read_text()
        cr_path.write_text(cr_text.replace("## Status: OPEN", "## Status: RESOLVED"))
        cr["status"] = "RESOLVED"

        # Hash all docs in final state
        hashes = {str(p): sha256(p) for p in all_paths}

        # Collect docs still held by other open CRs
        other_open_docs: set[str] = set()
        for oid, ocr in change_records.items():
            if oid == cr_id or ocr.get("status") != "OPEN":
                continue
            other_open_docs.update(ocr.get("touched_docs", []))

        # Restore stage status — only if ALL output files in the stage
        # are clear (not held by any other open CR).
        stages = manifest.get("stages", {})
        restored_stages: set[str] = set()
        skipped_stages: set[str] = set()

        # First pass: update doc hashes for files this CR cleared
        for p in touched:
            p_str = str(p)
            match = find_stage_for_doc(stages, p_str)
            if match:
                _, stage_data = match
                if not isinstance(stage_data.get("doc_hash"), dict):
                    stage_data["doc_hash"] = {}
                stage_data["doc_hash"][p_str] = hashes[p_str]

        # Second pass: decide per-stage whether to restore
        for p in touched:
            p_str = str(p)
            match = find_stage_for_doc(stages, p_str)
            if not match:
                continue
            stage_key, stage_data = match
            if stage_key in restored_stages or stage_key in skipped_stages:
                continue
            # Check ALL output files for this stage, not just the ones
            # this CR touched — another CR may hold a different file.
            output = stage_data.get("output")
            all_outputs = output if isinstance(output, list) else [output] if output else []
            blocked_files = [o for o in all_outputs if o in other_open_docs]
            if blocked_files:
                skipped_stages.add(stage_key)
                for bf in blocked_files:
                    print(f"  {bf}: kept as pending_approval "
                          f"(held by another open CR)")
                print(f"  stage {stage_key}: NOT restored "
                      f"(other outputs still pending)")
                continue
            restored_stages.add(stage_key)
            stage_data["status"] = "approved"
            stage_data.setdefault("approvals", []).append({
                "by": approver, "role": role, "date": today,
                "doc_hash": hashes, "via_cr": cr_id,
            })

        cr_module = cr.get("module", "UNKNOWN")
        print(f"Change record {cr_id} RESOLVED.")
        print(f"  Module:    {cr_module}")
        print(f"  Approvals: {len(cr['approvals'])}/{required} "
              f"(roles: {', '.join(sorted(filled_roles))})")
        print(f"  Docs restored to approved:")
        for sk in sorted(restored_stages):
            print(f"    stage {sk}")
    else:
        remaining = ["/".join(sorted(s)) for s in slots if not (s & filled_roles)]
        print(f"Change record {cr_id} — approval recorded (not yet resolved).")
        print(f"  Approvals so far: {len(cr['approvals'])}/{required}")
        print(f"  Still needed: {', '.join(remaining) or 'more approvals'}")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    git_commit(all_paths + [MANIFEST_PATH],
               f"chore(daksh): approve {cr_id} — {approver} ({role})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage")
    parser.add_argument("module", nargs="?", default=None)
    parser.add_argument("--approver", required=True)
    parser.add_argument("--revise", action="store_true")
    parser.add_argument("--reason", default=None)
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        sys.exit("ERROR: No Daksh pipeline found. Run `/daksh init` first.")

    manifest = json.loads(MANIFEST_PATH.read_text())

    # CR-NNN approval path
    if CR_ID_RE.match(args.stage):
        if args.revise:
            sys.exit("ERROR: --revise is not supported for change records. "
                     "Edit the CR document directly and re-run /daksh change.")
        approve_cr(manifest, args.stage, args.approver)
        return

    key = resolve_key(args.stage, args.module, manifest)

    # Roster check
    roster = {m["name"]: m["role"] for m in manifest.get("team_roster", [])}
    if args.approver not in roster:
        sys.exit(f"ERROR: '{args.approver}' is not in the team roster.")
    role = roster[args.approver]
    if not role_can_approve(role, key, manifest):
        sys.exit(f"ERROR: Role '{role}' cannot approve stage '{key}'.")

    # Stage state check
    stages = manifest.get("stages", {})
    if key not in stages:
        sys.exit(f"ERROR: Stage '{key}' not registered in manifest.")
    stage_data = stages[key]
    status = stage_data.get("status")

    if not args.revise:
        if status == "not_started":
            sys.exit(f"ERROR: Stage '{key}' has not been run yet. Generate the document first.")
        if status == "approved":
            output = stage_data.get("output")
            output_paths_check = [Path(p) for p in (output if isinstance(output, list) else [output])]
            stored_hashes = stage_data.get("doc_hash") or {}
            stale = any(
                stored_hashes.get(str(p)) != sha256(p)
                for p in output_paths_check if p.exists()
            )
            if not stale:
                sys.exit(f"ERROR: Stage '{key}' is already approved and documents are unchanged.")

    # Resolve output file(s) — only operate on files that have already been hashed.
    # In merged stages (e.g. 40a+40c per-module), a member doc may not exist yet.
    output = stage_data.get("output")
    all_output_paths = [Path(p) for p in (output if isinstance(output, list) else [output])]
    doc_hash = stage_data.get("doc_hash") or {}
    output_paths = [p for p in all_output_paths if str(p) in doc_hash]
    for p in output_paths:
        if not p.exists():
            sys.exit(f"ERROR: Output file not found: {p}")

    today = date.today().isoformat()

    # --- Revision path ---
    if args.revise:
        reason = args.reason or "No reason provided."
        stage_data["status"] = "revision_needed"
        stage_data.setdefault("revision_history", []).append({
            "flagged_by": args.approver,
            "role": role,
            "date": today,
            "reason": reason,
        })
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
        git_commit(
            [MANIFEST_PATH],
            f"chore(daksh): flag {args.stage} for revision — {args.approver} ({role})",
        )
        print(f"Revision flagged: {args.stage} ({key})")
        print(f"  By:     {args.approver} ({role})")
        print(f"  Reason: {reason}")
        print(f"  Status: revision_needed")
        print(f"\nThe stage must be re-run before it can be approved again.")
        return

    # --- Approval path ---

    # Stage 50 (impl) precondition: all module tasks must be done in traceability
    if key.startswith("50:"):
        module_from_key = key.split(":", 1)[1]
        traceability = manifest.get("traceability", {})
        # Find all TASK-<MODULE>-NNN entries
        module_prefix = f"TASK-{module_from_key}-"
        incomplete = [
            tid for tid, val in traceability.items()
            if tid.startswith(module_prefix) and (
                (isinstance(val, dict) and str(val.get("status", "")).lower() != "done")
                or (isinstance(val, str) and val.lower() != "done")
            )
        ]
        if incomplete:
            listing = "\n  ".join(sorted(incomplete))
            sys.exit(
                f"ERROR: Cannot approve impl {module_from_key} — "
                f"{len(incomplete)} task(s) not done:\n  {listing}\n"
                f"Mark all tasks done in manifest.traceability before approving."
            )

    # Open questions check (before touching the doc)
    warnings = []
    oq_policy = manifest.get("rules", {}).get("open_questions", "optional")
    for p in output_paths:
        count = count_open_questions(p)
        if count > 0:
            if oq_policy == "mandatory":
                sys.exit(f"ERROR: {count} unresolved open question(s) in {p}. Resolve before approving.")
            warnings.append(f"WARNING — {count} unresolved open question(s) in {p} (optional — approved anyway).")

    # Write approval block into each output document first, then hash the final state
    required = manifest.get("rules", {}).get("approvals_per_gate", 1)
    projected_count = len(stage_data.get("approvals", [])) + 1
    status = "approved" if projected_count >= required else "pending_approval"

    pre_hash = sha256(output_paths[0])  # hash before writing, used in the block label
    approval_block = (
        f"\nApproved by: {args.approver}\n"
        f"Role:        {role}\n"
        f"Date:        {today}\n"
        f"Hash:        {pre_hash[:12]}…\n"
    )
    for p in output_paths:
        text = p.read_text()
        if "## Approval" in text:
            pre, _ = text.split("## Approval", 1)
            p.write_text(pre + "## Approval\n" + approval_block)
        else:
            p.write_text(text.rstrip() + "\n\n## Approval\n" + approval_block)

    # Hash the doc in its final state (with approval block written)
    hashes = {str(p): sha256(p) for p in output_paths}

    approval_entry = {"by": args.approver, "role": role, "date": today, "doc_hash": hashes}
    stage_data.setdefault("approvals", []).append(approval_entry)
    current_count = len(stage_data["approvals"])

    if current_count >= required:
        stage_data["status"] = "approved"
        stage_data["doc_hash"] = hashes
    else:
        stage_data["status"] = "pending_approval"

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    commit_msg = f"chore(daksh): approve {args.stage} — {args.approver} ({role})"
    git_commit(output_paths + [MANIFEST_PATH], commit_msg)

    for path_str, h in hashes.items():
        print(f"  Document:  {path_str}")
        print(f"  Hash:      {h[:12]}…")
    print(f"  By:        {args.approver} ({role})")
    print(f"  Date:      {today}")
    print(f"  Approvals: {current_count}/{required}")
    print(f"  Status:    {stage_data['status']}")
    for w in warnings:
        print(f"\n{w}")


if __name__ == "__main__":
    main()
