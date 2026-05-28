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
        "body": (
            "## The 2026 financial crisis\n\n"
            "ICCSD's 2026 has been dominated by an unfolding financial-"
            "management crisis. The public arc of the year, drawn from "
            "the board record:\n\n"
            "- **January 2026** — the district's financial crisis was first "
            "  surfaced to the board (per public commenters at the May 26 "
            "  meeting). The board subsequently issued a *Board Financial "
            "  Leadership Update* outlining commitments — including an "
            "  organizational-chart review using outside expertise and a "
            "  policy revision (Policy 303.2) to add board involvement in "
            "  administrator hiring.\n"
            "- **February 17, 2026** — Audit RFP for FY2024-2028 discussed "
            "  at Board Work Session — first formal board acknowledgment of "
            "  the multi-year audit backlog. "
            "  ([meeting](../meetings/2026/2026-02-17-board-work-session-amended-agenda.md))\n"
            "- **February 24, 2026** — FY27 Certified Budget Update and "
            "  Proposed Budget Actions presented. "
            "  ([meeting](../meetings/2026/2026-02-24-regular-meeting-of-the-board-of-directors-amended-agenda.md))\n"
            "- **March 3, 2026** — Special board meeting reviewed Budget "
            "  Reduction Proposals and authorized FY26 Anticipatory "
            "  Warrants — a short-term borrowing instrument that the May 26 "
            "  public-comment period referenced as a sign of strain. "
            "  ([meeting](../meetings/2026/2026-03-03-special-board-meeting-5-00-pm-amended-agenda.md))\n"
            "- **March 24, 2026** — Public hearing on the Proposed FY27 "
            "  Property Tax Levy. "
            "  ([meeting](../meetings/2026/2026-03-24-special-meeting-budget-hearing-public-hearing-on-proposed-pr.md))\n"
            "- **April 1, 2026** — District announced a new CFO. "
            "  (Pat Moore — actual start date ~May 18, 2026 per her own "
            "  remarks at May 26.)\n"
            "- **May 2026** — Three district properties (Hills, ESC at 1725 "
            "  N. Dodge Street, and ~42.4 acres of Scanlon-family unimproved "
            "  real estate) sold and proceeds deposited into the General "
            "  Fund.\n"
            "- **May 26, 2026** — New CFO Pat Moore's first official "
            "  meeting. Audit catch-up plan presented: FY24 audit to be "
            "  brought to the board in July 2026, FY25 by November 2026, "
            "  FY26 by the March 31, 2027 statutory deadline, with FY23 "
            "  restatement also in progress. "
            "  ([transcript](../meetings/2026/transcripts/2026-05-26-regular-meeting-of-the-board-of-directors-amended-agenda.md))\n\n"
            "Multiple public commenters at recent meetings have referenced "
            "potential school closures and further cuts in the year ahead. "
            "Those are speakers' framings — not formal board actions on the "
            "record yet — and are noted here as context, not as facts.\n"
        ),
        "questions": [
            "What does the FY24 audit, when presented in July 2026, say "
            "about ICCSD's actual financial position?",
            "How much will be raised by the three 2026 property sales, and "
            "how is it being applied?",
            "What does the FY27 line-item budget look like once Pat Moore's "
            "new monthly close process and full audit results are "
            "incorporated?",
            "How has the property-tax levy moved year over year, and what "
            "drove the changes?",
        ],
    },
    "superintendent": {
        "title": "Superintendent",
        "keywords": [
            "superintendent", "interim superintendent", "search firm",
            "leadership transition", "Search Committee", "Degner",
        ],
        "intro": (
            "The superintendent's role, evaluation, and any transitions. This "
            "page collects discussions of the superintendent's performance, "
            "search and selection processes, contracts, and evaluations."
        ),
        "body": (
            "## The 2026 transition\n\n"
            "Matt Degner is ICCSD's Superintendent of record going into "
            "2026. The year unfolded into a leadership transition closely "
            "intertwined with the district's [financial crisis](budget.md):\n\n"
            "- **Friday, May 23, 2026** — Superintendent Degner publicly "
            "  announced via community email both his resignation as "
            "  Superintendent and his request to transition to a different "
            "  executive-level role within the district: Executive Director "
            "  of Secondary Schools. (Referenced by name and date in "
            "  multiple May 26 public comments; the original email is not "
            "  in the board's published agenda materials.)\n"
            "- **May 26, 2026 — board vote on Degner's transition.** The "
            "  personnel-agenda item containing the EDSS role change was "
            "  pulled from the consent agenda by Director Lingo and voted "
            "  on separately. The motion carried **5–2**: Directors "
            "  Abraham, Eastham, Horn-Frasier, and Malone voting yes; "
            "  Directors Finch and Lingo voting no. Lingo's stated "
            "  objection on the record: the role was offered a two-year "
            "  contract instead of one. Finch concurred. "
            "  ([transcript at vote](../meetings/2026/transcripts/2026-05-26-regular-meeting-of-the-board-of-directors-amended-agenda.md))\n"
            "- **May 26, 2026 — Interim Superintendent search discussed.** "
            "  Grundmeier (the firm that conducted the recent CFO search) "
            "  presented three engagement levels — recruitment-only, "
            "  full-service interim search, or a combined interim + "
            "  permanent engagement. Board consensus: the interim should "
            "  not be eligible for the permanent role, and the permanent "
            "  search should be a separate engagement decision.\n\n"
            "## Context from public comment\n\n"
            "The May 26 meeting included roughly 30 minutes of public "
            "comment opposing Degner's transition without an open search. "
            "Repeated themes from commenters (these are speakers' "
            "characterizations, not board findings):\n\n"
            "- ICCSD has fallen in statewide academic rankings during "
            "  Degner's tenure (one commenter cited a drop from ~159th "
            "  to ~241st of 300 Iowa districts based on NCES / Iowa Dept. "
            "  of Education / Census data).\n"
            "- The board's previously committed organizational-chart "
            "  review and Policy 303.2 revision should occur **before** "
            "  any administrative hires or restructurings, not after.\n"
            "- Multiple commenters alleged a pattern of retaliation, "
            "  hostile workplace conditions, and procedural irregularities "
            "  under current administrators. Specific names cited by "
            "  commenters are intentionally omitted from this archive "
            "  page; see the [transcript](../meetings/2026/transcripts/2026-05-26-regular-meeting-of-the-board-of-directors-amended-agenda.md) "
            "  for the verbatim record.\n\n"
            "These are public-comment claims. The archive surfaces them as "
            "part of the record without endorsing or refuting any of them.\n"
        ),
        "questions": [
            "What were the terms of Degner's superintendent contract, and "
            "what are the terms of the approved EDSS contract?",
            "What is the timeline and scope of the Interim Superintendent "
            "search via Grundmeier, and when is a permanent search "
            "expected?",
            "Did the board complete the organizational-chart review and "
            "Policy 303.2 revision that the Financial Leadership Update "
            "committed to, before or after the May 26 vote?",
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

    # Newest first throughout — readers want the most recent activity at
    # the top of any date-sorted list. Within a single meeting, attachments
    # still flow in section order (A, B, C...) which is the natural reading
    # order of the underlying agenda.
    meetings_sorted = sorted(matched_mids.values(),
                             key=lambda x: x["date"], reverse=True)
    atts_sorted = sorted(matched_attachments,
                         key=lambda x: (x["date"], x["att"]["section"]),
                         reverse=True)

    lines = [
        f"# {spec['title']}",
        "",
        spec["intro"],
        "",
    ]
    if spec.get("body"):
        lines.append(spec["body"])
        lines.append("")
    lines.extend([
        "## 2026 meetings on this topic",
        "",
    ])
    if not meetings_sorted:
        lines.append("_No 2026 meetings matched the keyword set yet._")
    else:
        for m in meetings_sorted:
            slug_m = slugify(m["title"])
            rel_path = f"../meetings/2026/{m['date']}-{slug_m}.md"
            lines.append(f"- **{m['date']}** — [{m['title']}]({rel_path})")
    lines.extend([
        "",
        "## 2026 documents on this topic",
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
        "Questions worth digging into across the underlying records:",
        "",
    ])
    for q in spec["questions"]:
        lines.append(f"- {q}")

    lines.extend([
        "",
        "---",
        "",
        f"*Meeting and document lists above are derived by keyword match "
        f"against the 2026 attachment index "
        f"([data/attachments_2026.json]"
        f"(https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/data/attachments_2026.json)) — "
        f"so the lists update automatically as the archive expands. "
        f"Page generated {generated_at}.*",
        "",
    ])
    return "\n".join(lines)


def build_topics_index(out_dir: Path) -> None:
    lines = [
        "# Topics",
        "",
        "Topic pages stitch related decisions across many meetings. Each "
        "page leads with a neutral overview of the topic, then lists every "
        "2026 meeting and supporting document that referenced it — with "
        "direct deep-links back to the district portal.",
        "",
        "The meeting and document lists are derived programmatically from "
        "the [2026 attachment index](https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/data/attachments_2026.json) "
        "by keyword match, so they stay in sync as the archive expands.",
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
