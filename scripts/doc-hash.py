#!/usr/bin/env python3
"""
daksh doc-hash — token-cheap content hashes for Daksh docs.

Default output is a 10-character base62 encoding of the SHA-256 of each
file's bytes. The point is **token economy for the LLM that reads and
writes the manifest**: a 64-char hex SHA-256 tokenises to ~16 BPE tokens
of opaque slop; a 10-char base62 form tokenises to ~3-4. Across a
manifest with several stages and revision histories, that compounds.

Base62 packs ~5.95 bits per character, so 10 chars carries ~60 bits —
a 50/50 collision needs ~10^9 distinct documents, well past any single
project's lifetime. Inside one project the LLM-facing hash never
collides; that is the only collision domain that matters here.

The audit-grade hash inside approve.py and preflight.py uses full hex
SHA-256 (256 bits) because the gate defends against intentional drift,
not accidental collision. There the adversary model has ~60 bits to
forge against if the gate is shortened — feasible — so the gate keeps
all 256 bits. Use `--full` to emit that form when updating the
`doc_hash` field in a manifest, which approve.py and preflight.py
compare against the full digest.

Usage:
  python scripts/doc-hash.py <file> [<file> ...]
  python scripts/doc-hash.py docs/business-requirements.md
  python scripts/doc-hash.py docs/*.md
  python scripts/doc-hash.py --json docs/business-requirements.md
  python scripts/doc-hash.py --full docs/business-requirements.md

Exit codes:
  0  all files hashed
  1  one or more files missing or unreadable
  2  bad arguments
"""

import argparse
import hashlib
import json
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


def short_hash(path: Path) -> str:
    digest_int = int(hashlib.sha256(path.read_bytes()).hexdigest(), 16)
    encoded = encode_base62(digest_int)
    # The digest is effectively uniform, so any 10-char slice is uniform.
    # Leading slice keeps lexical ordering closer to numeric.
    return encoded[:SHORT_LEN].rjust(SHORT_LEN, "0")


def full_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="doc-hash",
        description="Emit token-cheap 10-char base62 SHA-256 hashes for Daksh docs. "
                    "Pass --full for the gate-check hex digest.",
    )
    parser.add_argument("files", nargs="+", help="Files to hash.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON object keyed by path instead of two-column text.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Emit the full 64-char hex SHA-256 instead of the 10-char base62 short form. "
             "Use this when updating manifest doc_hash fields, which approve.py and "
             "preflight.py compare against the full digest.",
    )
    args = parser.parse_args(argv)

    hasher = full_hash if args.full else short_hash

    results: dict[str, str] = {}
    errors: list[str] = []
    for raw in args.files:
        p = Path(raw)
        if not p.is_file():
            errors.append(f"missing: {raw}")
            continue
        try:
            results[str(p)] = hasher(p)
        except OSError as exc:
            errors.append(f"unreadable: {raw} ({exc})")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for path, h in results.items():
            print(f"{h}  {path}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
