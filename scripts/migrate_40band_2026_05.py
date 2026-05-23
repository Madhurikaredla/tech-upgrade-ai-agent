#!/usr/bin/env python3
"""One-shot migration: rename 40-band stage codes in a manifest.

Mapping:
  40b:*      -> 40c:*    (TRD)
  40c:*      -> 40d:*    (Tasks)
  40a+40b:*  -> 40a+40c:* (legacy PRD+TRD merge, renamed under new codes)

Also: ensure each module entry has `stages_selected` and `stages_merged`
fields. Default selection for existing modules is inferred from the stages
that already exist in `manifest.stages` for that module.

Usage:
  python scripts/migrate_40band_2026_05.py <manifest_path>

Writes a .bak alongside the manifest on first run, never overwrites a
.bak. Idempotent: re-running on an already-migrated manifest is a no-op.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

# Rename rules: (old_prefix, new_prefix). Order matters — apply longest first
# so '40a+40b' is rewritten before '40b' alone.
RENAMES = [
    ("40a+40b", "40a+40c"),
    ("40c",     "40d"),
    ("40b",     "40c"),
]

STAGE_KEY_RE = re.compile(r"^([0-9a-z+]+)(:.*)?$")
MODULE_BAND_PREFIXES = {"40a", "40b", "40c", "40d"}


def rename_prefix(key: str) -> str:
    """Rewrite a stage key like '40b:AUTH' -> '40c:AUTH'."""
    m = STAGE_KEY_RE.match(key)
    if not m:
        return key
    prefix, suffix = m.group(1), m.group(2) or ""
    for old, new in RENAMES:
        if prefix == old:
            return f"{new}{suffix}"
    return key


def migrate_dict_keys(d: dict) -> dict:
    """Rewrite top-level keys of a dict according to RENAMES."""
    return {rename_prefix(k): v for k, v in d.items()}


def migrate_combined(combined: list[str]) -> list[str]:
    return [rename_prefix(k) for k in combined]


def infer_stages_selected(stages: dict, module: str) -> list[str]:
    """For a module, return the 40-band stages already present (post-rename)."""
    suffix = f":{module}"
    selected: set[str] = set()
    for key in stages.keys():
        if not key.endswith(suffix):
            continue
        prefix = key[: -len(suffix)]
        for member in prefix.split("+"):
            if member in MODULE_BAND_PREFIXES:
                selected.add(member)
    return sorted(selected)


def infer_stages_merged(stages: dict, module: str) -> list[list[str]]:
    """For a module, return merge groups inferred from compound stage keys."""
    suffix = f":{module}"
    merged: list[list[str]] = []
    for key in stages.keys():
        if not key.endswith(suffix):
            continue
        prefix = key[: -len(suffix)]
        members = prefix.split("+")
        if len(members) > 1 and all(m in MODULE_BAND_PREFIXES for m in members):
            merged.append(sorted(members))
    return merged


def collect_modules(stages: dict) -> set[str]:
    modules: set[str] = set()
    for key in stages.keys():
        _, sep, mod = key.partition(":")
        if sep and mod and any(
            p in MODULE_BAND_PREFIXES or p == "50" for p in key.split(":", 1)[0].split("+")
        ):
            modules.add(mod)
    return modules


def migrate(manifest: dict) -> dict:
    # 1. Rename stages map.
    if "stages" in manifest and isinstance(manifest["stages"], dict):
        manifest["stages"] = migrate_dict_keys(manifest["stages"])

    # 2. Rename stages_combined list (and rename the field for clarity — keep
    #    as-is for now to avoid breaking unknown readers).
    rules = manifest.get("rules", {})
    if "stages_combined" in rules:
        rules["stages_combined"] = migrate_combined(rules["stages_combined"])

    # 3. Rename any other manifest sections that key by stage code.
    #    `org.governance.stage_authority` keys are stage prefixes — rename.
    gov = manifest.get("org", {}).get("governance", {})
    if "stage_authority" in gov and isinstance(gov["stage_authority"], dict):
        gov["stage_authority"] = {
            rename_prefix(k): v for k, v in gov["stage_authority"].items()
        }

    # 4. Backfill per-module stages_selected and stages_merged.
    modules_field = manifest.setdefault("module_config", {})
    stages = manifest.get("stages", {})
    for module in collect_modules(stages):
        entry = modules_field.setdefault(module, {})
        if "stages_selected" not in entry:
            entry["stages_selected"] = infer_stages_selected(stages, module)
        if "stages_merged" not in entry:
            entry["stages_merged"] = infer_stages_merged(stages, module)

    return manifest


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: migrate_40band_2026_05.py <manifest_path>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"manifest not found: {path}", file=sys.stderr)
        return 2
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"backup written: {bak}")
    original = json.loads(path.read_text())
    migrated = migrate(json.loads(path.read_text()))
    if migrated == original:
        print(f"{path}: no changes (already migrated)")
        return 0
    path.write_text(json.dumps(migrated, indent=2) + "\n")
    print(f"{path}: migrated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
