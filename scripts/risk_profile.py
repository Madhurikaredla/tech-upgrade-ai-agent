#!/usr/bin/env python3
"""risk_profile.py — project-wide Daksh risk scanner.

Usage:
    python scripts/risk_profile.py                      # print report
    python scripts/risk_profile.py --save               # also write docs/.daksh/risk-report.md
    python scripts/risk_profile.py --accept-risk RISK-001 --acknowledged-by Alice
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_PATH = Path("docs/.daksh/manifest.json")
REPORT_PATH = Path("docs/.daksh/risk-report.md")


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        sys.exit("ERROR: No Daksh pipeline found. Run `/daksh init` first.")
    try:
        return json.loads(MANIFEST_PATH.read_text())
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: Invalid manifest JSON: {exc}")


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


# ── scanners ──────────────────────────────────────────────────────────────────

def scan_pending_approval(manifest: dict) -> list[dict]:
    """Every planning stage that is pending_approval is HIGH risk."""
    items = []
    for key, stage in manifest.get("stages", {}).items():
        if stage.get("status") == "pending_approval":
            items.append({
                "severity": "HIGH",
                "category": "Unapproved stage",
                "detail": f"Stage {key} was produced but not approved",
                "action": f"`/daksh approve {key.replace(':', ' ').lower()}`",
            })
    return items


def scan_open_crs(manifest: dict) -> list[dict]:
    """Open change records (spec in flux) and discovery records (legacy constraints found)."""
    items = []
    for cr_id, cr in manifest.get("change_records", {}).items():
        if cr.get("status") != "OPEN":
            continue
        if cr.get("type") == "discovery":
            items.append({
                "severity": "MEDIUM",
                "category": "Open discovery record",
                "detail": f"{cr_id} [{cr.get('module', '?')}] {cr.get('title', '')} — legacy constraint unresolved",
                "action": f"Fill in DR and resolve via `docs/implementation/{cr.get('module', 'MODULE')}/change-records/{cr_id}.md`",
            })
        else:
            items.append({
                "severity": "HIGH",
                "category": "Open change record",
                "detail": f"{cr_id} is OPEN — affected docs are unresolved",
                "action": f"`/daksh approve {cr_id}`",
            })
    return items


def scan_stale_hashes(manifest: dict) -> list[dict]:
    """Output docs that exist on disk but whose hash differs from the manifest."""
    items = []
    import hashlib
    for key, stage in manifest.get("stages", {}).items():
        doc_hash = stage.get("doc_hash") or {}
        for path_str, expected in doc_hash.items():
            p = Path(path_str)
            if not p.exists():
                continue
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual != expected:
                items.append({
                    "severity": "MEDIUM",
                    "category": "Stale hash",
                    "detail": f"{path_str} changed since last approval (stage {key})",
                    "action": "Re-approve the stage or raise a CR",
                })
    return items


def scan_missing_outputs(manifest: dict) -> list[dict]:
    """Stages marked approved but whose output files are missing."""
    items = []
    for key, stage in manifest.get("stages", {}).items():
        if stage.get("status") != "approved":
            continue
        output = stage.get("output")
        paths = output if isinstance(output, list) else [output] if output else []
        for p_str in paths:
            if p_str and not Path(p_str).exists():
                items.append({
                    "severity": "MEDIUM",
                    "category": "Missing output",
                    "detail": f"{p_str} (stage {key}) is approved but file not found on disk",
                    "action": "Regenerate or restore the file",
                })
    return items


def scan_risk_register(manifest: dict) -> list[dict]:
    """Open (unacknowledged) risk register entries — HIGH severity."""
    items = []
    for entry in manifest.get("risk_register", []):
        if entry.get("status") == "open":
            items.append({
                "severity": "HIGH",
                "category": "Risk register",
                "detail": f"[{entry['risk_id']}] {entry['reason']} (stage {entry['stage']})",
                "action": f"`/daksh risk-profile --accept-risk {entry['risk_id']} --acknowledged-by <name>`",
            })
    return items


def scan_inherited(manifest: dict) -> list[dict]:
    """Inherited stages — acknowledged at init, always visible as LOW (amber)."""
    items = []
    for entry in manifest.get("risk_register", []):
        if entry.get("type") == "inherited" and entry.get("status") == "acknowledged":
            ref = entry.get("inherited_ref") or "unknown"
            items.append({
                "severity": "LOW",
                "category": "Inherited stage",
                "detail": f"[{entry['risk_id']}] Stage {entry['stage']} defers to pre-Daksh artifact: {ref}",
                "action": f"`/daksh approve {entry['stage']}` to formally approve, or carry as acknowledged",
            })
    return items


# ── formatting ────────────────────────────────────────────────────────────────

SEV_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def format_report(items: list[dict], project: str) -> str:
    lines = [
        f"# Risk Report — {project}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]
    if not items:
        lines += ["**No open risks.** All stages approved and docs in sync.", ""]
        return "\n".join(lines)

    by_sev: dict[str, list[dict]] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for item in items:
        by_sev.setdefault(item["severity"], []).append(item)

    for sev in ("HIGH", "MEDIUM", "LOW"):
        group = by_sev.get(sev, [])
        if not group:
            continue
        lines.append(f"## {sev} ({len(group)})")
        lines.append("")
        for item in group:
            lines.append(f"**{item['category']}** — {item['detail']}")
            lines.append(f"→ {item['action']}")
            lines.append("")

    total = len(items)
    lines += [
        "---",
        f"Total open risks: {total}  ",
        "Acknowledge a risk: `/daksh risk-profile --accept-risk RISK-NNN --acknowledged-by <name>`",
        "",
    ]
    return "\n".join(lines)


# ── accept-risk ───────────────────────────────────────────────────────────────

def accept_risk(manifest: dict, risk_id: str, acknowledged_by: str) -> None:
    register = manifest.get("risk_register", [])
    for entry in register:
        if entry["risk_id"] == risk_id:
            if entry["status"] == "acknowledged":
                print(f"{risk_id} is already acknowledged.")
                return
            entry["status"] = "acknowledged"
            entry["acknowledged_by"] = acknowledged_by
            entry["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            save_manifest(manifest)
            print(f"✓ {risk_id} acknowledged by {acknowledged_by}.")
            return
    sys.exit(f"ERROR: {risk_id} not found in risk_register.")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accept-risk", metavar="RISK-ID",
                        help="Mark a risk as acknowledged")
    parser.add_argument("--acknowledged-by", metavar="NAME",
                        help="Who is acknowledging the risk")
    parser.add_argument("--save", action="store_true",
                        help=f"Write report to {REPORT_PATH}")
    args = parser.parse_args()

    manifest = load_manifest()

    if args.accept_risk:
        if not args.acknowledged_by:
            sys.exit("ERROR: --acknowledged-by is required with --accept-risk")
        accept_risk(manifest, args.accept_risk, args.acknowledged_by)
        return 0

    items = (
        scan_risk_register(manifest)
        + scan_pending_approval(manifest)
        + scan_open_crs(manifest)
        + scan_stale_hashes(manifest)
        + scan_missing_outputs(manifest)
        + scan_inherited(manifest)
    )
    # Deduplicate by detail string (risk_register entries overlap with pending_approval scan)
    seen: set[str] = set()
    deduped = []
    for item in items:
        if item["detail"] not in seen:
            seen.add(item["detail"])
            deduped.append(item)
    deduped.sort(key=lambda x: SEV_ORDER.get(x["severity"], 99))

    project = manifest.get("project", "Daksh Project")
    report = format_report(deduped, project)
    print(report)

    if args.save:
        REPORT_PATH.write_text(report)
        print(f"Report saved to {REPORT_PATH}")

    return 1 if any(i["severity"] == "HIGH" for i in deduped) else 0


if __name__ == "__main__":
    raise SystemExit(main())
