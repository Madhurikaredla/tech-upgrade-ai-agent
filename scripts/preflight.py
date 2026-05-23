#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_PATH = Path("docs/.daksh/manifest.json")

# Stage codes per `daksh` command. 40-band stages are per-module selectable and
# mergeable; merges are read from manifest.modules[MODULE].stages_merged.
STAGE_MAP = {
    "onboard":  "00",
    "vision":   "10",
    "brd":      "20",
    "roadmap":  "30",
    "ops":      "35",
    "prd":      "40a:{}",
    "solution": "40b:{}",
    "trd":      "40c:{}",
    "tasks":    "40d:{}",
    "impl":     "50:{}",
}

# Module-band stages that exist on the linear backbone for prior-stage gating.
# Solution (40b) is intentionally off-chain — it is optional per module and its
# PRD gate is enforced inside the stage's own CONTEXT.md, not via prior-stage
# walks here.
LINEAR_CHAIN = ["00+10", "20", "30", "35", "40a", "40c", "40d", "50"]

# Module-band stage prefixes used by pending-approval checks.
MODULE_BAND_PREFIXES = ("40a", "40b", "40c", "40d")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merge_group_for(manifest: dict, module: str, stage_prefix: str) -> list[str] | None:
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


PROJECT_LEVEL_PREFIXES = {"00", "10", "20", "30", "00+10", "60"}


def prior_stage_key(key: str) -> str | None:
    """Return the prior stage key on the linear backbone, or None.

    For merged stages (e.g. '40a+40c:AUTH'), uses the earliest member's
    position in the chain — i.e. the prior stage is whatever sits before the
    *first* merged member. The prior stage is module-scoped only if the prior
    chain entry is module-level; project-level priors (e.g. '30') drop the
    module suffix.
    """
    prefix, _, module = key.partition(":")
    members = prefix.split("+")
    chain_positions = [LINEAR_CHAIN.index(m) for m in members if m in LINEAR_CHAIN]
    if not chain_positions:
        return None
    earliest = min(chain_positions)
    if earliest == 0:
        return None
    prior = LINEAR_CHAIN[earliest - 1]
    if prior in PROJECT_LEVEL_PREFIXES:
        return prior
    return f"{prior}:{module}" if module else prior


def module_from_key(key: str) -> str | None:
    _, _, module = key.partition(":")
    return module or None


def task_file_for_module(module: str) -> Path:
    return Path(f"docs/implementation/{module}/tasks.md")


def iter_task_dependencies(tasks_path: Path) -> list[tuple[str, list[str]]]:
    entries: list[tuple[str, list[str]]] = []
    current_task: str | None = None
    for line in tasks_path.read_text().splitlines():
        heading = re.match(r"^####\s+(TASK-[A-Z0-9-]+):", line)
        if heading:
            current_task = heading.group(1)
            continue
        depends = re.match(r"^- \*\*Depends on:\*\*\s*(.+)$", line)
        if current_task and depends:
            raw = depends.group(1).strip()
            if raw.lower() == "none":
                entries.append((current_task, []))
            else:
                deps = [part.strip() for part in raw.split(",") if part.strip()]
                entries.append((current_task, deps))
            current_task = None
    return entries


def git_working_tree_clean() -> bool:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    return completed.returncode == 0 and not completed.stdout.strip()


def result(level: str, message: str, hard: bool = False) -> dict:
    return {"level": level, "message": message, "hard": hard}


def iter_output_paths(output: str | list[str] | None) -> list[Path]:
    if not output:
        return []
    return [Path(p) for p in (output if isinstance(output, list) else [output])]


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        sys.exit("ERROR: No Daksh pipeline found. Run /daksh init first.")
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: Invalid manifest JSON: {exc}")


def resolve_stage_entry(stages: dict, key: str) -> tuple[str, dict] | None:
    """Find the stage entry that satisfies *key*, accounting for merged stages.

    If `key` matches verbatim, return it. Otherwise:
    - For project-level combined keys like '00+10', check if `key` is a member
      of the combined prefix (handles small weight-class combined stages).
    - For module-scoped keys like '40c:JIRA', look for any '<group>:JIRA'
      where 40c is a member of the merge group.
    """
    if key in stages:
        return key, stages[key]
    # Handle project-level combined stages (e.g. "00" covered by "00+10")
    key_prefix = key.split(":")[0]
    for k, v in stages.items():
        k_prefix = k.split(":")[0]
        if key_prefix in k_prefix.split("+") and ":" not in key:
            return k, v
    prefix, sep, module = key.partition(":")
    if not sep:
        return None
    suffix = f":{module}"
    for k, v in stages.items():
        if not k.endswith(suffix):
            continue
        kprefix = k[: -len(suffix)]
        if prefix in kprefix.split("+"):
            return k, v
    return None


def base_checks(manifest: dict, key: str) -> list[dict]:
    checks = [result("PASS", "Manifest exists")]
    stages = manifest.get("stages", {})
    resolved_current = resolve_stage_entry(stages, key)
    if not resolved_current:
        return checks + [result("FAIL", f"Stage {key} not registered in manifest", True)]
    resolved_key_current, _ = resolved_current
    if resolved_key_current != key:
        checks.append(result("PASS", f"Stage {key} resolved via combined stage {resolved_key_current}"))
    else:
        checks.append(result("PASS", f"Stage {key} registered in manifest"))
    prior_key = prior_stage_key(key)
    if not prior_key:
        return checks
    resolved = resolve_stage_entry(stages, prior_key)
    if not resolved:
        # Prior stage absent from manifest — intentionally skipped for this weight class.
        checks.append(result("WARN",
                             f"Prior stage {prior_key} not in manifest — skipped for this project's pipeline"))
        return checks
    resolved_key, prior = resolved
    if resolved_key != prior_key:
        checks.append(result("PASS",
                             f"Prior stage {prior_key} resolved via merge group {resolved_key}"))
        prior_key = resolved_key
    prior_mode = prior.get("mode", "greenfield")
    if prior_mode == "inherited":
        ref = prior.get("inherited_ref") or "no ref recorded"
        checks.append(result("PASS",
                             f"Prior stage {prior_key} is inherited (acknowledged) — ref: {ref}"))
        return checks
    required = manifest.get("rules", {}).get("approvals_per_gate", 1)
    approvals = len(prior.get("approvals", []))
    approved = approvals >= required
    checks.append(result("PASS" if approved else "WARN",
                         f"Prior stage {prior_key} approved: {approvals}/{required}",
                         False))
    hard_hash = key.startswith("50:")
    for path in iter_output_paths(prior.get("output")):
        exists = path.exists()
        checks.append(result("PASS" if exists else ("FAIL" if hard_hash else "WARN"),
                             f"{path} exists on disk", hard_hash and not exists))
        expected = (prior.get("doc_hash") or {}).get(str(path))
        if exists and expected:
            matches = sha256(path) == expected
            level = "PASS" if matches else ("FAIL" if hard_hash else "WARN")
            checks.append(result(level, f"{path} hash matches manifest", hard_hash and not matches))
    return checks


def pending_approval_checks(manifest: dict, module: str) -> list[dict]:
    """Fail if any module planning stage is pending_approval.

    Checks the authoritative source (stage status in manifest) first.
    Then cross-references change_records for a helpful diagnostic message,
    but the block decision is based on stage state, not CR metadata.
    """
    checks: list[dict] = []
    stages = manifest.get("stages", {})
    change_records = manifest.get("change_records", {})

    # Build a reverse index: doc_path -> CR-ID for open CRs (diagnostic only)
    cr_by_doc: dict[str, str] = {}
    for cr_id, cr in change_records.items():
        if cr.get("status") != "OPEN":
            continue
        for doc in cr.get("touched_docs", []):
            cr_by_doc[doc] = cr_id

    # Check each module-band stage (single or merged) for pending_approval.
    # We scan all stages whose key starts with any 40-band prefix and ends
    # with `:{module}` — this covers both singles ('40a:AUTH') and merges
    # ('40a+40c:AUTH') without enumerating every possible merge combination.
    suffix = f":{module}"
    found_pending = False
    for stage_key, stage_data in stages.items():
        if not stage_key.endswith(suffix):
            continue
        prefix = stage_key[:-len(suffix)]
        members = prefix.split("+")
        if not any(m in MODULE_BAND_PREFIXES for m in members):
            continue
        if stage_data.get("status") != "pending_approval":
            continue
        found_pending = True
        # Try to identify the CR responsible for diagnostic clarity
        output = stage_data.get("output")
        output_paths = output if isinstance(output, list) else [output] if output else []
        cr_hint = None
        for p in output_paths:
            if p in cr_by_doc:
                cr_hint = cr_by_doc[p]
                break
        msg = f"Stage {stage_key} is pending_approval"
        if cr_hint:
            msg += f" (via {cr_hint}). Run `/daksh approve {cr_hint}` first"
        checks.append(result("WARN", msg, False))

    if not found_pending:
        checks.append(result("PASS", f"No pending_approval stages for {module}"))

    return checks


def impl_checks(manifest: dict, key: str, task_id: str | None = None) -> list[dict]:
    is_clean = git_working_tree_clean()
    checks = [result("PASS" if is_clean else "FAIL", "Git working tree clean", not is_clean)]
    module = module_from_key(key)
    if not module:
        return checks

    # Check for pending_approval docs from open CRs
    checks.extend(pending_approval_checks(manifest, module))
    traceability = manifest.get("traceability")
    if not isinstance(traceability, dict):
        return checks + [result("FAIL", "Manifest traceability map missing", True)]

    all_deps = iter_task_dependencies(task_file_for_module(module))

    if task_id:
        # Task-scoped: only check dependencies for the specified task
        task_deps = [(tid, deps) for tid, deps in all_deps if tid == task_id]
        if not task_deps:
            checks.append(result("FAIL",
                                 f"{task_id} not found in tasks.md — cannot verify dependencies",
                                 True))
    else:
        # Fallback: module-wide (no task specified — warn about reduced precision)
        task_deps = all_deps
        if task_deps:
            checks.append(result("WARN",
                                 "No TASK-ID provided — checking all module dependencies "
                                 "(pass --task TASK-ID for precise checks)"))

    for tid, dependencies in task_deps:
        if not dependencies:
            continue
        for dependency in dependencies:
            trace = traceability.get(dependency, "")
            if isinstance(trace, dict):
                done = str(trace.get("status", "")).lower() == "done"
            else:
                done = str(trace).lower() == "done"
            message = (
                f"{tid} dependency {dependency} done"
                if done else f"{tid} dependency {dependency} not done"
            )
            checks.append(result("PASS" if done else "FAIL", message, not done))
    return checks


def write_risk_entries(manifest: dict, stage_key: str, checks: list[dict]) -> None:
    """Append a risk register entry for each WARN check, deduplicating by message."""
    warns = [c for c in checks if c["level"] == "WARN"]
    if not warns:
        return
    register = manifest.setdefault("risk_register", [])
    existing_msgs = {e["reason"] for e in register}
    now = datetime.now(timezone.utc).isoformat()
    seq = len(register) + 1
    for w in warns:
        if w["message"] in existing_msgs:
            continue
        register.append({
            "risk_id": f"RISK-{seq:03d}",
            "stage": stage_key,
            "reason": w["message"],
            "detected_at": now,
            "status": "open",
            "acknowledged_by": None,
            "acknowledged_at": None,
        })
        existing_msgs.add(w["message"])
        seq += 1
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def print_table(stage: str, module: str | None, checks: list[dict],
                manifest: dict | None = None, key: str = "") -> int:
    label = f"{stage} {module.upper()}" if module else stage
    hard_failures = sum(1 for c in checks if c["hard"] and c["level"] == "FAIL")
    warnings = sum(1 for c in checks if c["level"] == "WARN")
    print(f"Preflight: {label}".rstrip())
    print("─" * 49)
    for check in checks:
        print(f"[{check['level']}] {check['message']}")
    print("─" * 49)
    if hard_failures:
        verdict = "BLOCKED"
    elif warnings:
        verdict = "WARN"
    else:
        verdict = "PASS"
    print(f"Result: {verdict} — {hard_failures} hard failure(s), {warnings} warning(s)")
    if warnings and manifest is not None:
        write_risk_entries(manifest, key, checks)
        print("  ↳ Risk entries written to manifest.risk_register — run `/daksh risk-profile` to review")
    return 1 if hard_failures else 0


def run_checks(manifest: dict, key: str, task_id: str | None = None) -> list[dict]:
    checks = base_checks(manifest, key)
    if key.startswith("50:"):
        checks.extend(impl_checks(manifest, key, task_id))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage")
    parser.add_argument("module", nargs="?", default=None)
    parser.add_argument("--task", default=None,
                        help="TASK-ID to scope dependency checks (impl stage only)")
    args = parser.parse_args()
    manifest = load_manifest()
    key = resolve_key(args.stage, args.module, manifest)
    return print_table(args.stage, args.module,
                       run_checks(manifest, key, args.task),
                       manifest=manifest, key=key)


if __name__ == "__main__":
    raise SystemExit(main())
