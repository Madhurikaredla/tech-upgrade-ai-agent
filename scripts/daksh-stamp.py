#!/usr/bin/env python3
"""
daksh-stamp — update a stage's doc_hash field in docs/.daksh/manifest.json.

Why this exists: the gate-check field stages.<n>.doc_hash is full hex
SHA-256, which costs ~16 tokens every time the LLM has to write it into
the manifest by hand. This script lets the LLM say `daksh-stamp 30`
instead — the full hex never has to round-trip through assistant output.

Behaviour:
  - Reads docs/.daksh/manifest.json (override with --manifest).
  - Resolves stages.<n>.output to a file path; refuses if it's a list
    unless --output names which file to stamp.
  - Computes the full hex SHA-256 of that file.
  - If it matches the existing doc_hash, exits 0 with a no-op message.
  - Otherwise: writes the new hex into doc_hash, and if --note is given,
    appends a revision-history entry { date: today, note: <text>
    " Short hash: <10-char base62>." }.
  - Atomic write via tmp file + os.replace.
  - Never touches git. Never changes stage status.

Usage:
  python scripts/daksh-stamp.py <stage> [--note "<text>"] [--output <path>]
                                        [--manifest <path>] [--dry-run]

Examples:
  python scripts/daksh-stamp.py 30
  python scripts/daksh-stamp.py 30 --note "Added §Technology Baseline."
  python scripts/daksh-stamp.py 60 --output handbook/admin.md --note "..."

Exit codes:
  0  stamped, or already up to date
  1  manifest / stage / file lookup failed
  2  bad arguments
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
from pathlib import Path

BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
SHORT_LEN = 10


def encode_base62(n: int) -> str:
    if n == 0:
        return "0"
    out = []
    while n:
        n, rem = divmod(n, 62)
        out.append(BASE62[rem])
    return "".join(reversed(out))


def hash_full(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_short(data: bytes) -> str:
    digest_int = int(hashlib.sha256(data).hexdigest(), 16)
    return encode_base62(digest_int)[:SHORT_LEN].rjust(SHORT_LEN, "0")


def resolve_output(stage_entry: dict, stage_id: str, override: str | None) -> str:
    output = stage_entry.get("output")
    if output is None:
        raise SystemExit(f"stage {stage_id} has no 'output' field")
    if isinstance(output, list):
        if override is None:
            raise SystemExit(
                f"stage {stage_id} has multiple outputs {output!r}; "
                f"pass --output <path> to name which file to stamp"
            )
        if override not in output:
            raise SystemExit(
                f"--output {override!r} is not listed in stage {stage_id} outputs {output!r}"
            )
        return override
    if override is not None and override != output:
        raise SystemExit(
            f"--output {override!r} does not match stage {stage_id} output {output!r}"
        )
    return output


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="daksh-stamp")
    p.add_argument("stage", help="Stage number (e.g. 30, 40c).")
    p.add_argument("--note", help="Revision-history note text. Omit for a silent resync.")
    p.add_argument("--output", help="Which output to stamp (required if stage.output is a list).")
    p.add_argument("--manifest", default="docs/.daksh/manifest.json",
                   help="Path to manifest.json (default: docs/.daksh/manifest.json from CWD).")
    p.add_argument("--dry-run", action="store_true",
                   help="Compute and report; do not write the manifest.")
    args = p.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    # docs/.daksh/manifest.json -> manifest.json (parent) -> .daksh (parent) -> docs (parent) -> repo root
    manifest_root = manifest_path.resolve().parent.parent.parent
    manifest = json.loads(manifest_path.read_text())

    stages = manifest.get("stages", {})
    if args.stage not in stages:
        print(f"ERROR: stage {args.stage!r} not in manifest.stages "
              f"(have: {sorted(stages)})", file=sys.stderr)
        return 1

    stage_entry = stages[args.stage]
    output_rel = resolve_output(stage_entry, args.stage, args.output)
    output_path = (manifest_root / output_rel).resolve()
    if not output_path.is_file():
        print(f"ERROR: output file not found: {output_path}", file=sys.stderr)
        return 1

    data = output_path.read_bytes()
    new_full = hash_full(data)
    new_short = hash_short(data)
    old_full = stage_entry.get("doc_hash")

    if old_full == new_full:
        print(f"no-op stage {args.stage}: already stamped {new_short} ({output_rel})")
        return 0

    stage_entry["doc_hash"] = new_full
    if args.note:
        today = _dt.date.today().isoformat()
        note_text = args.note.rstrip()
        if not note_text.endswith("."):
            note_text += "."
        note_text += f" Short hash: {new_short}."
        stage_entry.setdefault("revision_history", []).append(
            {"date": today, "note": note_text}
        )

    if args.dry_run:
        print(f"would stamp stage {args.stage}: {new_short} ({output_rel})"
              + (" + revision note" if args.note else ""))
        return 0

    tmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, manifest_path)
    print(f"stamped stage {args.stage}: {new_short} ({output_rel})"
          + (" + revision note" if args.note else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
