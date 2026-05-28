"""Mirror the curated News_<YEAR>.md from the ICCSD client folder into
the published site at docs/press/<year>.md.

The source file is hand-maintained by the archive author in the ICCSD
client folder (outside this repo). This script:

  1. Reads the source markdown
  2. Strips any pre-existing MkDocs frontmatter (so re-runs are idempotent)
  3. Prepends the standard frontmatter the site expects
  4. Writes to docs/press/<year>.md

Run after editing the source file:

    python scripts/build_press.py \\
        --source "C:/Users/.../ICCSD/2026/News_2026.md" \\
        --year 2026 \\
        --out docs/press/2026.md

The published page keeps the source file's structure (chronological by
month, with an index at the bottom). All cross-page links from the rest
of the site to specific months (e.g. `press/2026.md#may-2026`) stay
valid as long as the source's `## January 2026` style headings remain.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FRONTMATTER_TEMPLATE = """---
title: {year} News Coverage
---

"""


# Strip a YAML frontmatter block at the very top of a markdown file, if
# present. Idempotent: lets re-running this script not stack frontmatters.
_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, required=True,
                    help="Path to the hand-maintained News_<YEAR>.md")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True,
                    help="Output path docs/press/<year>.md")
    args = ap.parse_args()

    if not args.source.exists():
        print(f"ERROR: source file not found: {args.source}")
        return 2

    raw = args.source.read_text(encoding="utf-8")
    # Strip any existing frontmatter so the mirror is canonical.
    body = _FRONTMATTER_RE.sub("", raw)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = FRONTMATTER_TEMPLATE.format(year=args.year) + body
    args.out.write_text(payload, encoding="utf-8", newline="\n")

    n_articles = len(re.findall(r"^### ", body, re.MULTILINE))
    print(f"Mirrored {args.source.name} -> {args.out}")
    print(f"  {len(payload):,} bytes, {n_articles} articles by H3 count.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
