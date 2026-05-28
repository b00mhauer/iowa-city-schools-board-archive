"""Generate draft topic pages by keyword-matching against the AID index.

Each topic gets:
  - An editorial intro (hand-written, lives in TOPIC_TEMPLATES below)
  - "Relevant meetings" — meetings whose attachments match any keyword
  - "Relevant documents" — direct deep-links to specific docs that matched

The output is clearly marked DRAFT. The maintainer is expected to prune,
re-order, and add narrative. This script makes the *starting point* useful
instead of empty.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


# Keyword sets: ordered roughly from most-specific to most-generic; tune as
# the corpus evolves. Matching is case-insensitive substring on
# attachment.title, attachment.filename, and attachment.item_title.
TOPICS: dict[str, dict] = {
    "budget": {
        "title": "Budget",
        "keywords": [
            "budget", "tax levy", "appropriations", "general fund",
            "spending authority", "fiscal year", "FY26", "FY27", "audit report",
            "financial report", "expenditure", "ESSA", "ESSER",
        ],
        "intro": (
            "How ICCSD raises and spends money — annual budgets, property tax "
            "levies, audits, fund balances, and significant transfers. The "
            "Financial Oversight Committee meets monthly and most line items "
            "land in regular board meetings as consent-agenda approvals."
        ),
        "questions": [
            "What is the multi-year trend in the general-fund balance and "
            "spending authority?",
            "How has the property-tax levy moved year over year, and what "
            "drove the changes?",
            "Where are the largest discretionary line items, and how have they "
            "shifted?",
        ],
    },
    "superintendent": {
        "title": "Superintendent",
        "keywords": [
            "superintendent", "interim superintendent", "search firm",
            "leadership transition", "Search Committee",
        ],
        "intro": (
            "The superintendent's role, evaluation, and any transitions. This "
            "page collects discussions of the superintendent's performance, "
            "search and selection processes, contracts, and evaluations."
        ),
        "questions": [
            "What is the current superintendent's contract and evaluation cycle?",
            "Have there been recent leadership transitions, and what process "
            "was used to fill them?",
        ],
    },
    "facilities": {
        "title": "Facilities",
        "keywords": [
            "facility", "facilities", "construction", "renovation", "building",
            "ESC", "Educational Services Center", "school sale",
            "property sale", "Hills property", "Dodge Street",
            "Scanlon", "lease", "real estate", "capital project",
            "PPEL", "SAVE",
        ],
        "intro": (
            "Buildings, land, and capital projects — new construction, "
            "renovations, property sales and purchases, leases, and the "
            "PPEL / SAVE funding streams that pay for them."
        ),
        "questions": [
            "What major capital projects are underway or planned?",
            "What district-owned properties have been sold, and where did the "
            "proceeds go?",
        ],
    },
    "policies": {
        "title": "Policies",
        "keywords": [
            "Policy", "policies", "first reading", "second reading",
            "third reading", "policy adoption", "policy revision",
            "P&G", "Policy & Governance", "policy update",
        ],
        "intro": (
            "Board policy adoptions, revisions, and rescissions. ICCSD uses a "
            "multi-reading process; policy changes typically appear at the "
            "Policy & Governance Committee, then at one or more regular board "
            "meetings before final adoption."
        ),
        "questions": [
            "Which board policies have been amended or adopted in the past "
            "12 months?",
            "What policies are currently in the multi-reading pipeline?",
        ],
    },
    "boundaries": {
        "title": "Boundaries",
        "keywords": [
            "boundary", "boundaries", "attendance area", "redistricting",
            "open enrollment", "school assignment",
        ],
        "intro": (
            "School attendance areas, boundary changes, and open-enrollment "
            "decisions. ICCSD's open-enrollment line items appear in nearly "
            "every regular board meeting as routine consent-agenda items; "
            "boundary changes themselves are rarer and more consequential."
        ),
        "questions": [
            "When were the current attendance boundaries last revised, and "
            "what drove the change?",
            "How does the open-enrollment process work, and what are typical "
            "approval/denial patterns?",
        ],
    },
}


def matches(text: str, keywords: list[str]) -> list[str]:
    """Return the keywords that appear (case-insensitively) in text."""
    lower = (text or "").lower()
    return [kw for kw in keywords if kw.lower() in lower]


def parse_date(title_dt: str) -> str:
    """Return YYYY-MM-DD or empty string."""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", title_dt or "")
    if not m:
        return ""
    mm, dd, yy = m.groups()
    return f"{yy}-{int(mm):02d}-{int(dd):02d}"


_SLUG_BAD = re.compile(r"[^a-z0-9]+")


def slugify(s: str, max_len: int = 60) -> str:
    s = s.lower()
    s = _SLUG_BAD.sub("-", s).strip("-")
    return s[:max_len].rstrip("-") or "meeting"


def meeting_page_link(date_str: str, title: str) -> str:
    slug = slugify(title)
    return f"../meetings/2026/{date_str}-{slug}.md"


def build_topic_page(slug: str, spec: dict, attachments_data: dict,
                     generated_at: str) -> str:
    """Compose the topic page."""
    matched_attachments: list[dict] = []
    matched_mids: dict[int, dict] = {}

    for mid_str, rec in attachments_data.items():
        mid = int(mid_str)
        meeting_match = False
        for att in rec["attachments"]:
            haystack = f"{att.get('title','')} {att.get('filename','')} {att.get('item_title','')}"
            kws = matches(haystack, spec["keywords"])
            if kws:
                matched_attachments.append({
                    "mid": mid,
                    "title": rec["title"],
                    "date": parse_date(rec["title_datetime"]),
                    "att": att,
                    "matched_keywords": kws,
                })
                meeting_match = True
        if meeting_match:
            matched_mids.setdefault(mid, {
                "mid": mid,
                "title": rec["title"],
                "date": parse_date(rec["title_datetime"]),
                "source_url": rec["source_url"],
            })

    meetings_sorted = sorted(matched_mids.values(), key=lambda x: x["date"])
    atts_sorted = sorted(matched_attachments, key=lambda x: (x["date"], x["att"]["section"]))

    lines = [
        f"# {spec['title']}",
        "",
        "!!! warning \"Draft — pending editorial review\"",
        "",
        "    This page is auto-generated from keyword matches against the 2026",
        "    attachment index. It's a starting point, not a finished page.",
        "    Items below may be relevant or may be incidental keyword hits.",
        "    See [Methodology](../methodology.md) for the editorial standard.",
        "",
        "## Overview",
        "",
        spec["intro"],
        "",
        "## Relevant meetings (2026)",
        "",
    ]
    if not meetings_sorted:
        lines.append("_No 2026 meetings matched the keyword set yet._")
    else:
        for m in meetings_sorted:
            slug_m = slugify(m["title"])
            rel_path = f"../meetings/2026/{m['date']}-{slug_m}.md"
            lines.append(f"- **{m['date']}** — [{m['title']}]({rel_path})")
    lines.extend([
        "",
        "## Relevant documents",
        "",
        "Direct deep-links to specific supporting documents on the district portal.",
        "",
    ])
    if not atts_sorted:
        lines.append("_No 2026 documents matched the keyword set yet._")
    else:
        # Cap to avoid runaway pages; if more, ask reader to browse meetings.
        SHOW = 50
        for m in atts_sorted[:SHOW]:
            att = m["att"]
            kws = ", ".join(m["matched_keywords"])
            lines.append(
                f"- **{m['date']}** — [{att['title']}]({att['url']}) "
                f"_(matched: {kws})_"
            )
        if len(atts_sorted) > SHOW:
            lines.append("")
            lines.append(
                f"_{len(atts_sorted) - SHOW} more matched documents not shown — "
                f"browse the meetings above to see them in context._"
            )

    lines.extend([
        "",
        "## Open questions",
        "",
    ])
    for q in spec["questions"]:
        lines.append(f"- {q}")

    lines.extend([
        "",
        "---",
        "",
        f"*Auto-generated draft on {generated_at}. "
        f"{len(meetings_sorted)} matching meeting(s), "
        f"{len(matched_attachments)} matching document(s) found by keyword search. "
        f"Curated content will replace this list as the topic page is written.*",
        "",
    ])
    return "\n".join(lines)


def build_topics_index(out_dir: Path) -> None:
    lines = [
        "# Topics",
        "",
        "Topic pages stitch related decisions across many meetings. They are "
        "the most editorial part of the archive — the maintainer's reading "
        "of the record, with citations to every meeting and document so "
        "claims can be checked.",
        "",
        "!!! note \"Draft state\"",
        "",
        "    All topic pages are currently auto-generated drafts from a "
        "keyword scan of 2026 meetings. Expect them to evolve substantially "
        "as they are curated.",
        "",
        "## Current topics",
        "",
    ]
    for slug, spec in TOPICS.items():
        lines.append(f"- [{spec['title']}]({slug}.md) — {spec['intro'][:120]}...")
    lines.extend(["", ""])
    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--attachments", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="docs/topics/")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    with open(args.attachments, encoding="utf-8") as f:
        data = json.load(f)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    build_topics_index(args.out)
    for slug, spec in TOPICS.items():
        page = build_topic_page(slug, spec, data, generated_at)
        (args.out / f"{slug}.md").write_text(page, encoding="utf-8")
        print(f"Wrote {args.out / (slug + '.md')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
