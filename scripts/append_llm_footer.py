"""Append a one-line LLM-navigation footer to every markdown file in docs/.

When an AI tool fetches a single page's raw markdown, it doesn't know
anything else exists. This footer tells the AI where the site-wide
manifest lives so it can navigate from any page to any other.

The footer is marked with an HTML comment so re-runs are idempotent —
files that already have the footer are skipped.

Designed to run AFTER all other generators in the refresh chain, so the
freshly-regenerated topic pages, timeline, home page, manifest, etc.
each get the footer appended.

Skipped:
  - llms.md itself (it IS the manifest; would be circular)
  - any file already carrying the footer marker

Usage:

    python scripts/append_llm_footer.py --docs-dir docs/
"""

from __future__ import annotations

import argparse
from pathlib import Path


# HTML comment marker — invisible in rendered HTML, sentinel for idempotency.
FOOTER_MARKER = "<!-- LLM_FOOTER_v1 -->"

MANIFEST_RAW_URL = (
    "https://raw.githubusercontent.com/b00mhauer/iowa-city-schools-board-archive"
    "/main/docs/llms.md"
)

FOOTER_BLOCK = f"""
---

{FOOTER_MARKER}
*For AI tools reading this page: the site-wide index of every other page
in this archive — meetings, topics, board members, press articles,
supporting documents — is at <{MANIFEST_RAW_URL}>. Fetch it for
cross-page context if the conversation calls for it.*
"""


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--docs-dir", type=Path, required=True,
                    help="Path to docs/")
    args = ap.parse_args()

    if not args.docs_dir.is_dir():
        print(f"ERROR: not a directory: {args.docs_dir}")
        return 2

    updated = 0
    already = 0
    skipped = 0

    for md in args.docs_dir.rglob("*.md"):
        # Skip the manifest itself — pointless self-reference.
        if md.name == "llms.md":
            skipped += 1
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  WARN: could not read {md}: {e}")
            continue
        if FOOTER_MARKER in text:
            already += 1
            continue
        # Append the footer, cleanly newline-terminated.
        if not text.endswith("\n"):
            text += "\n"
        text += FOOTER_BLOCK
        md.write_text(text, encoding="utf-8", newline="\n")
        updated += 1

    print(f"LLM footer: updated {updated}, already-had {already}, "
          f"skipped {skipped}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
