"""Generate docs/llms.md — the LLM manifest / table-of-contents.

This is the file the AI tools are pointed at for cross-page context.
It's a single markdown document that lists every meaningful page in
the archive with a one-line description and the raw markdown URL.

Following the emerging community convention at https://llmstxt.org/
(simplified — we keep everything inside the MkDocs docs/ tree so it
deploys as part of the site, and reference raw GitHub URLs so AI tools
fetching it get clean markdown rather than the rendered HTML).

The manifest auto-regenerates daily via refresh_press.py.

Inputs:
  - data/summaries_<year>.json — for the meeting list with previews
  - docs/press/<year>.md       — for the press article count
  - docs/anchor_events_<year>.json — for anchor events
  - data/attachments_<year>.json — for the supporting-doc count
  - ICCSD all_meetings.json — for meeting dates and titles

Output: docs/llms.md
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RAW_BASE = (
    "https://raw.githubusercontent.com/b00mhauer/iowa-city-schools-board-archive"
    "/main/docs"
)


def slugify(s: str, max_len: int = 60) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len].rstrip("-") or "meeting"


def first_sentence(s: str, max_chars: int = 160) -> str:
    """Return a clean opening clause from a summary."""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = s.replace("\\n", " ").replace("\n", " ").strip()
    m = re.search(r"^(.+?[.!?])(\s|$)", s)
    out = m.group(1).strip() if m else s
    if len(out) > max_chars:
        out = out[:max_chars].rsplit(" ", 1)[0] + "…"
    return out


def render_manifest(year: int, summaries: dict, all_meetings: list[dict],
                    press_md: str, attachments: dict,
                    anchors: dict) -> str:
    """Build the manifest markdown."""
    refreshed = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    article_count = press_md.count("\n### ")
    doc_count = sum(len(r.get("attachments", [])) for r in attachments.values())
    meeting_count = sum(
        1 for m in all_meetings
        if isinstance(m.get("DateTime"), str)
        and m.get("DateTime", "").startswith(f"{year}-")
        and m.get("IsPublic")
    )

    # Per-meeting lines, newest first, only meetings with curated summaries
    by_mid = {m["MID"]: m for m in all_meetings if isinstance(m.get("MID"), int)}
    meeting_entries: list[tuple[str, str, str, str]] = []  # (date, title, url, preview)
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
        title = m.get("Title", "Meeting")
        slug = slugify(title)
        url = f"{RAW_BASE}/meetings/{year}/{d.strftime('%Y-%m-%d')}-{slug}.md"
        meeting_entries.append((
            d.strftime("%Y-%m-%d"),
            title,
            url,
            first_sentence(summary),
        ))
    meeting_entries.sort(key=lambda e: e[0], reverse=True)

    # Anchor events: hand-curated pre-crisis facts
    anchor_lines: list[str] = []
    for e in anchors.get("events", []):
        date = e.get("date", "")
        title = e.get("title", "")
        summary = e.get("summary", "")
        anchor_lines.append(f"- **{date}** — {title}. {first_sentence(summary)}")

    out: list[str] = []
    out.append("---")
    out.append("title: LLM Manifest")
    out.append("---")
    out.append("")
    out.append("# Iowa City Schools Board Archive — LLM Manifest")
    out.append("")
    out.append(
        "This file is a machine-readable index of the archive, intended for "
        "AI tools (ChatGPT, Gemini, Perplexity, Claude, etc.). It lists every "
        "page worth reading with a one-line description and a direct link to "
        "the raw markdown. Humans landing here are welcome to read it too — "
        "it's a useful site map — but the structured site is at "
        f"<https://b00mhauer.github.io/iowa-city-schools-board-archive/>."
    )
    out.append("")
    out.append(f"**Refreshed:** {refreshed}. Regenerates daily.")
    out.append("")
    out.append(
        f"**At a glance:** {meeting_count} public board meetings in {year}, "
        f"{doc_count} supporting documents, {article_count} press articles, "
        f"5 topic pages, 7 current board members."
    )
    out.append("")
    out.append("---")
    out.append("")

    # --- Site structure ---
    out.append("## Site structure")
    out.append("")
    out.append(f"- **[Home]({RAW_BASE}/index.md)** — site overview, latest meeting summary, recent press coverage.")
    out.append(f"- **[Timeline]({RAW_BASE}/timeline.md)** — chronological dashboard of every {year} event (meetings, press articles, anchor events) sorted newest first.")
    out.append(f"- **[How to use]({RAW_BASE}/how-to-use.md)** — guide to navigating the four browse modes (meeting, topic, timeline, search).")
    out.append(f"- **[Methodology]({RAW_BASE}/methodology.md)** — how the archive is built, what's primary source vs. synthesis, auto-refresh process.")
    out.append(f"- **[About]({RAW_BASE}/about.md)** — purpose, scope, roadmap.")
    out.append("")

    # --- Topics ---
    out.append("## Topics")
    out.append("")
    out.append("Each topic page has: a stable overview, an auto-generated list of {year} meetings on that topic, an auto-generated list of supporting documents, and an auto-generated press coverage section. All update daily.".replace("{year}", str(year)))
    out.append("")
    out.append(f"- **[Budget]({RAW_BASE}/topics/budget.md)** — annual budgets, property tax levies, audits, fund balances, and significant transfers (including the 2026 financial crisis).")
    out.append(f"- **[Superintendent]({RAW_BASE}/topics/superintendent.md)** — superintendent role, evaluation, contracts, and transitions.")
    out.append(f"- **[Facilities]({RAW_BASE}/topics/facilities.md)** — buildings, land, capital projects, property sales/purchases, leases, PPEL/SAVE funding.")
    out.append(f"- **[Policies]({RAW_BASE}/topics/policies.md)** — board policy adoptions, revisions, rescissions, and the Policy & Governance Committee pipeline.")
    out.append(f"- **[Boundaries]({RAW_BASE}/topics/boundaries.md)** — school attendance areas, boundary changes, open-enrollment patterns, and school-closure / reconfiguration discussions.")
    out.append("")

    # --- People ---
    out.append("## People")
    out.append("")
    out.append(f"- **[Board Members]({RAW_BASE}/people/board-members.md)** — all 7 current directors with committee roles, individual vote records, recurring themes, attributed quotes with transcript timestamps.")
    out.append(f"- **[Administrators]({RAW_BASE}/people/administrators.md)** — senior cabinet, executive cabinet, and directors. Notes active leadership transitions.")
    out.append("")

    # --- Press ---
    out.append("## Press")
    out.append("")
    out.append(f"- **[{year} Press Index]({RAW_BASE}/press/{year}.md)** — {article_count} curated news articles from KCRG, The Cedar Rapids Gazette, The Daily Iowan, CBS2 Iowa, Iowa Public Radio (NPR), Little Village, West Side Story, and others. Each entry: headline, publication, byline, date, summary, and direct link to the original article. Auto-refreshes daily.")
    out.append("")

    # --- Key documents ---
    out.append("## Key documents")
    out.append("")
    out.append(f"- **[Key Documents]({RAW_BASE}/documents/key-documents.md)** — curated by category (budget & financial, capital projects, property dispositions, labor agreements, active-review policies, leadership transition). Direct deep-links to the district portal.")
    out.append(f"- **[Audited Financial Statements]({RAW_BASE}/audited-financials/index.md)** — audited annual financial statements for ICCSD (FY2020–2023; FY2024–2025 missing as part of the audit backlog story) plus ~13 peer Iowa districts (Ankeny, Burlington, Cedar Rapids, Davenport, Des Moines, Dubuque, Johnston, Linn-Mar, Muscatine, Pleasant Valley, Waterloo, Waukee, West Des Moines) FY2020–2025. PDFs hosted directly on this site.")
    out.append("")

    # --- Anchor events ---
    if anchor_lines:
        out.append("## Anchor events (pre-crisis / out-of-band)")
        out.append("")
        out.append("Hand-curated facts that aren't directly in press articles or meeting summaries — added so the AI can place 2026 events in context.")
        out.append("")
        out.extend(anchor_lines)
        out.append("")

    # --- Meetings ---
    out.append("## Meetings with curated summaries (newest first)")
    out.append("")
    out.append(
        f"Each meeting page has: title, date, official agenda link, a "
        f"\"what happened\" editorial summary (where curated), a link to "
        f"the YouTube recording, and the full supporting-documents list "
        f"grouped by agenda item with direct deep-links to each PDF."
    )
    out.append("")
    for date, title, url, preview in meeting_entries:
        out.append(f"- **{date}** — [{title}]({url}) — {preview}")
    out.append("")

    # --- Interactive tools ---
    out.append("## Interactive tools")
    out.append("")
    out.append(f"- **[Chat with the Archive]({RAW_BASE}/chat-with-the-archive.md)** — landing page with pre-loaded ChatGPT, Gemini, and Perplexity prompts that open each AI tool with a question about a specific topic or page already typed in. The user just hits enter.")
    out.append("")

    # --- Footer note for AI tools ---
    out.append("---")
    out.append("")
    out.append("## Notes for AI tools reading this manifest")
    out.append("")
    out.append(
        "- All URLs above point to **raw markdown** sources on GitHub — "
        "clean text, no HTML styling, low token cost."
    )
    out.append(
        "- If a reader asks a question that spans multiple pages, fetch "
        "whichever combination of the above URLs is relevant. Cross-meeting "
        "and cross-topic questions are the use case the archive is designed for."
    )
    out.append(
        "- The site adds **no editorial characterization of its own** — every "
        "claim is attributed to its source (a meeting, a document, a news "
        "article, an anchor-event citation). When summarizing, preserve those "
        "attributions; don't replace them with your own framing."
    )
    out.append(
        "- When sources disagree (e.g., the district says one thing, a press "
        "article says another), present both with attribution rather than "
        "picking a winner."
    )
    out.append(
        "- Primary sources (PDFs on the district portal, YouTube recordings of "
        "meetings) are the ground truth. The archive's summaries and topic "
        "narratives are aids, not authority. When a user wants to verify a "
        "claim, point them to the primary source, not the summary."
    )
    out.append("")

    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--summaries", type=Path, required=True)
    ap.add_argument("--press", type=Path, required=True)
    ap.add_argument("--anchors", type=Path, required=True)
    ap.add_argument("--attachments", type=Path, required=True)
    ap.add_argument("--meetings-json", type=Path, required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    summaries = json.loads(args.summaries.read_text(encoding="utf-8")) \
        if args.summaries.exists() else {}
    press_md = args.press.read_text(encoding="utf-8") \
        if args.press.exists() else ""
    anchors = json.loads(args.anchors.read_text(encoding="utf-8")) \
        if args.anchors.exists() else {"events": []}
    attachments = json.loads(args.attachments.read_text(encoding="utf-8")) \
        if args.attachments.exists() else {}
    all_meetings = json.loads(args.meetings_json.read_text(encoding="utf-8")) \
        if args.meetings_json.exists() else []

    out = render_manifest(args.year, summaries, all_meetings,
                          press_md, attachments, anchors)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out, encoding="utf-8", newline="\n")
    print(f"Wrote {args.out} ({args.out.stat().st_size:,} bytes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
