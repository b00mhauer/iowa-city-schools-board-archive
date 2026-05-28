"""Regenerate the auto 'Latest activity' block on docs/index.md.

The home page has a marker section like:

    <!-- LATEST_ACTIVITY:START -->
    ... (auto-generated content) ...
    <!-- LATEST_ACTIVITY:END -->

This script replaces the contents between those markers with a fresh
snapshot showing:

  - the most-recent summarized meeting (one-line link + first sentence
    of its 'what happened' summary), and
  - the three most-recent press articles (date · publication · headline,
    each linked to the original).

Designed to be chained after refresh_press.py so the home page stays in
sync with the press file and meeting summaries every day.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


_MARKER_RE = re.compile(
    r"<!--\s*LATEST_ACTIVITY:START\s*-->.*?<!--\s*LATEST_ACTIVITY:END\s*-->",
    re.DOTALL,
)

_PRESS_H3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
_PRESS_META_RE = re.compile(
    r"^\*\*([^*]+?)\*\*\s*(?:—\s*([^—\n]+?))?\s*(?:—\s*\*([^*]+?)\*)?\s*$"
)

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_press_date(s: str, default_year: int) -> tuple[int, int, int]:
    """Return sort key (year, month, day) — 0 for unknown components."""
    s = (s or "").strip().strip("—").strip(",").strip()
    if not s:
        return (default_year, 0, 0)
    m = re.match(r"(\d{4})-(\d{1,2})(?:-(\d{1,2}))?", s)
    if m:
        y, mo, d = m.groups()
        return (int(y), int(mo), int(d) if d else 0)
    m = re.match(r"([A-Za-z]+)\s+(\d{1,2})(?:[/](\d{1,2}))?(?:,\s*(\d{4}))?", s)
    if m:
        mo_name, d1, _d2, y = m.groups()
        mo_lower = mo_name.lower().rstrip(".")
        if mo_lower in _MONTHS:
            return (int(y) if y else default_year, _MONTHS[mo_lower], int(d1))
    return (default_year, 0, 0)


def parse_press_articles(press_md: str, year: int) -> list[dict]:
    out: list[dict] = []
    lines = press_md.splitlines()
    i = 0
    while i < len(lines):
        m = _PRESS_H3_RE.match(lines[i])
        if not m:
            i += 1
            continue
        headline = m.group(1).strip().strip('"')
        publication = ""
        date_str = ""
        url = ""
        for j in range(1, 8):
            if i + j >= len(lines):
                break
            ln = lines[i + j].strip()
            if not ln:
                continue
            mp = _PRESS_META_RE.match(ln)
            if mp:
                publication = mp.group(1).strip()
                if mp.group(2):
                    date_str = mp.group(2).strip()
                continue
            mu = re.search(r"\((https?://[^)\s]+)\)", ln)
            if mu and not url:
                url = mu.group(1)
            if ln.startswith("## ") or ln.startswith("### "):
                break
        y, mo, d = parse_press_date(date_str, year)
        out.append({
            "headline": headline,
            "publication": publication,
            "date_display": date_str,
            "sort_key": (y, mo, d),
            "url": url,
        })
        i += 1
    return out


def first_sentence(s: str, max_chars: int = 320) -> str:
    """Return a clean opening clause from a summary string."""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = s.replace("\\n", " ").replace("\n", " ").strip()
    m = re.search(r"^(.+?[.!?])(\s|$)", s)
    out = m.group(1).strip() if m else s
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0] + "…"
    return out


def slugify(s: str, max_len: int = 60) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len].rstrip("-") or "meeting"


def latest_meeting(summaries: dict, all_meetings: list[dict],
                   year: int) -> dict | None:
    """Return the most recent year-N meeting that has a summary."""
    by_mid = {m["MID"]: m for m in all_meetings if isinstance(m.get("MID"), int)}
    best: dict | None = None
    best_sort: tuple[int, int, int] = (0, 0, 0)
    for mid_str, summary in summaries.items():
        try:
            mid = int(mid_str)
        except ValueError:
            continue
        m = by_mid.get(mid)
        if not m:
            continue
        dt = m.get("DateTime", "")
        try:
            d = datetime.strptime(dt[:10], "%Y-%m-%d")
        except Exception:
            continue
        if d.year != year:
            continue
        key = (d.year, d.month, d.day)
        if key > best_sort:
            best_sort = key
            best = {
                "title": m.get("Title", "Meeting"),
                "date": d.strftime("%B %d, %Y"),
                "date_iso": d.strftime("%Y-%m-%d"),
                "summary": first_sentence(summary),
                "slug": slugify(m.get("Title", "Meeting")),
            }
    return best


def render_block(meeting: dict | None, articles: list[dict], year: int) -> str:
    lines = [
        "<!-- LATEST_ACTIVITY:START -->",
        "<!-- This block is regenerated daily by scripts/build_home.py.",
        "     Don't edit the contents between START/END markers by hand. -->",
        "",
        "## Latest",
        "",
    ]
    if meeting:
        url = f"meetings/{year}/{meeting['date_iso']}-{meeting['slug']}.md"
        lines.append(
            f"**Most recent board meeting — {meeting['date']}:** "
            f"[{meeting['title']}]({url}). {meeting['summary']}"
        )
        lines.append("")

    if articles:
        lines.append("**Recent press coverage:**")
        lines.append("")
        for a in articles[:3]:
            date = a.get("date_display", "") or "—"
            pub = a.get("publication", "") or "(publication unknown)"
            head = a["headline"]
            url = a.get("url", "")
            if url:
                lines.append(f"- **{date}** — *{pub}* — [{head}]({url})")
            else:
                lines.append(f"- **{date}** — *{pub}* — {head}")
        lines.append("")
        lines.append(
            f"[Browse all {year} press coverage →](press/{year}.md) · "
            f"[Browse all {year} meetings →](meetings/{year}/index.md)"
        )
        lines.append("")

    lines.append("<!-- LATEST_ACTIVITY:END -->")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--index", type=Path, required=True,
                    help="Path to docs/index.md")
    ap.add_argument("--summaries", type=Path, required=True,
                    help="Path to data/summaries_<year>.json")
    ap.add_argument("--press", type=Path, required=True,
                    help="Path to docs/press/<year>.md")
    ap.add_argument("--meetings-json", type=Path, required=True,
                    help="Path to ICCSD all_meetings.json")
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()

    summaries = json.loads(args.summaries.read_text(encoding="utf-8")) \
        if args.summaries.exists() else {}
    press_md = args.press.read_text(encoding="utf-8") \
        if args.press.exists() else ""
    all_meetings = json.loads(args.meetings_json.read_text(encoding="utf-8")) \
        if args.meetings_json.exists() else []

    meeting = latest_meeting(summaries, all_meetings, args.year)
    articles = parse_press_articles(press_md, args.year)
    articles.sort(key=lambda a: a["sort_key"], reverse=True)

    block = render_block(meeting, articles, args.year)

    index_md = args.index.read_text(encoding="utf-8")
    if not _MARKER_RE.search(index_md):
        print(f"ERROR: {args.index} has no LATEST_ACTIVITY markers.",
              file=__import__("sys").stderr)
        return 2
    new_md = _MARKER_RE.sub(block, index_md)
    args.index.write_text(new_md, encoding="utf-8", newline="\n")
    print(f"Updated Latest block in {args.index}")
    if meeting:
        print(f"  Latest meeting: {meeting['date']} — {meeting['title'][:60]}")
    if articles:
        print(f"  Most recent article: {articles[0].get('date_display','')} — {articles[0]['headline'][:60]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
