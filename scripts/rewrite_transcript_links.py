"""Rewrite "transcript ~M:SS" style links in editorial pages to point
directly to YouTube with the timestamp anchor.

Background: the original editorial pages contained links like

    [2026-05-26 transcript ~29:17](../meetings/2026/2026-05-26-regular...md)

where the timestamp was useful only because the transcript page itself
had a YouTube anchor at that time. Now that transcripts are out of
docs/, the link target no longer matches the link text.

This script:
  1. Walks /corpus/transcripts/2026/ to build a {YYYY-MM-DD: youtube_url}
     mapping.
  2. Scans /docs/ for link patterns where the text contains a
     YYYY-MM-DD prefix and a ~HH:MM:SS or ~M:SS timestamp.
  3. Rewrites the URL to https://youtu.be/<video_id>?t=<seconds>.

Idempotent: re-running won't double-rewrite (it only replaces .md targets
that contain `/meetings/2026/`, not external URLs).
"""

from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).parent.parent.resolve()
CORPUS = REPO / "corpus" / "transcripts" / "2026"
DOCS = REPO / "docs"


def load_video_ids() -> dict[str, str]:
    """Walk corpus transcripts and return {YYYY-MM-DD: video_id}."""
    out: dict[str, str] = {}
    for p in CORPUS.glob("*.md"):
        date = p.stem[:10]  # YYYY-MM-DD prefix
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("**Video:**"):
                m = re.search(r"v=([\w-]+)", line)
                if m:
                    out[date] = m.group(1)
                break
    return out


def parse_timestamp(ts: str) -> int | None:
    """Parse '~M:SS' or '~H:MM:SS' (with optional ~) into total seconds."""
    ts = ts.lstrip("~").strip()
    parts = ts.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    return None


# Capture: [<text containing YYYY-MM-DD and ~M:SS or ~H:MM:SS>](<url containing /meetings/2026/>)
LINK_RE = re.compile(
    r"\[([^\]]*?(\d{4}-\d{2}-\d{2})[^\]]*?~(\d{1,2}(?::\d{2}){1,2})[^\]]*?)\]"
    r"\(([^)]*?/meetings/2026/[^)]*?\.md)\)"
)


def main() -> int:
    video_ids = load_video_ids()
    print(f"Loaded {len(video_ids)} (date -> video_id) mappings.")

    changed_files = 0
    rewrites = 0

    for md in DOCS.rglob("*.md"):
        if "meetings/2026/" in str(md):
            # Skip generated meeting pages — they should not have these links.
            continue
        s = md.read_text(encoding="utf-8")
        out: list[str] = []
        pos = 0

        def repl(m: re.Match) -> str:
            nonlocal rewrites
            text, date_str, ts_str, _url = m.group(1), m.group(2), m.group(3), m.group(4)
            vid = video_ids.get(date_str)
            if not vid:
                return m.group(0)  # leave untouched
            secs = parse_timestamp(ts_str)
            if secs is None:
                return m.group(0)
            rewrites += 1
            return f"[{text}](https://youtu.be/{vid}?t={secs})"

        new = LINK_RE.sub(repl, s)
        if new != s:
            md.write_text(new, encoding="utf-8", newline="\n")
            changed_files += 1

    print(f"Rewrote {rewrites} transcript-style links across {changed_files} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
