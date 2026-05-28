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
            "PPEL", "SAVE", "FMP", "auditorium", "Opstad",
        ],
        "intro": (
            "Buildings, land, and capital projects — new construction, "
            "renovations, property sales and purchases, leases, and the "
            "PPEL / SAVE funding streams that pay for them."
        ),
        "body": (
            "## Three property sales in 2026\n\n"
            "ICCSD moved three district-owned properties through the "
            "statutory public-hearing-and-conveyance process during 2026, "
            "with the proceeds of each sale directed to the General Fund:\n\n"
            "- **Hills property** — 301 W. Main Street, Hills, Iowa. "
            "  Public hearing and proceeds-deposit resolution adopted at "
            "  the [May 26, 2026 board meeting](../meetings/2026/2026-05-26-regular-meeting-of-the-board-of-directors-amended-agenda.md).\n"
            "- **Educational Services Center (ESC)** — 1725 N. Dodge "
            "  Street, Iowa City. Hearing-date set at the "
            "  [April 14 meeting](../meetings/2026/2026-04-14-regular-meeting-of-the-board-of-directors.md); "
            "  conveyance public hearing and authorizing resolution "
            "  adopted at the "
            "  [April 28 meeting](../meetings/2026/2026-04-28-regular-meeting-of-the-board-of-directors-amended-agenda.md); "
            "  proceeds deposit confirmed at the May 26 meeting alongside "
            "  the Hills and Scanlon sales.\n"
            "- **Scanlon parcel** — ~42.4 acres of unimproved real estate "
            "  previously purchased from Scanlon Family, L.L.C. Public "
            "  hearing and proceeds-deposit resolution adopted at the "
            "  May 26 meeting.\n\n"
            "All three sales were part of the year's larger response to "
            "the district's [unfolding financial-management crisis](budget.md).\n\n"
            "## Capital projects in flight\n\n"
            "- **Facilities Master Plan (FMP) resolution** — Director "
            "  Lingo led drafting and the motion at the "
            "  [May 12, 2026 meeting](../meetings/2026/2026-05-12-regular-meeting-of-the-board-of-directors.md). "
            "  Tracked through Financial Oversight Committee as a project-"
            "  prioritization tool.\n"
            "- **West HS Auditorium Improvements** — multi-meeting capital "
            "  project referenced from the [Jan 27 meeting](../meetings/2026/2026-01-27-regular-meeting-of-the-board-of-directors.md) "
            "  onward.\n"
            "- **City HS Auditorium / Opstad Theater Lighting Upgrades** "
            "  — discussed at the [March 10 meeting](../meetings/2026/2026-03-10-regular-meeting-of-the-board-of-directors.md).\n"
            "- **Capital Projects Status Report** — recurring report at 8 "
            "  of the 10 Financial Oversight + General meetings in 2026.\n"
            "- **Forevergreen Road easements** — Temporary Construction "
            "  Easement and Public Utilities Easement resolutions adopted "
            "  in stages across the [Jan 13](../meetings/2026/2026-01-13-regular-meeting-of-the-board-of-directors.md) "
            "  and [Jan 27](../meetings/2026/2026-01-27-regular-meeting-of-the-board-of-directors.md) meetings.\n\n"
            "## Funding streams\n\n"
            "ICCSD's capital work is funded primarily through PPEL "
            "(Physical Plant and Equipment Levy) and SAVE (Secure an "
            "Advanced Vision for Education / 1¢ statewide sales tax). "
            "Bonding capacity against these streams is a recurring "
            "discussion in Financial Oversight Committee, particularly "
            "around the FMP ranking work.\n"
        ),
        "questions": [
            "What are the realized proceeds from each of the three 2026 "
            "property sales, and exactly how is each tranche being applied?",
            "Where does the FMP project-ranking list currently stand, and "
            "which projects are funded vs. unfunded?",
            "How has PPEL / SAVE bonding capacity moved over the past "
            "three years, and what's the headroom for the next capital cycle?",
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
        "body": (
            "## How policy work flows at ICCSD\n\n"
            "Policy work originates in the **Policy & Governance Committee** "
            "— chaired in 2026 by Director Mitch Lingo (he succeeded prior "
            "chair Director Lisa Williams in January). Draft language is "
            "iterated in committee, then brought to a regular board meeting "
            "for review, action, or tabling. Most policy changes touch "
            "multiple meetings before adoption.\n\n"
            "## 2026 policy adoptions\n\n"
            "- **Policy 200.3G4 — Financial Oversight Committee Charter.** "
            "  Adopted at the "
            "  [May 26, 2026 meeting](../meetings/2026/2026-05-26-regular-meeting-of-the-board-of-directors-amended-agenda.md) "
            "  after several rounds in committee. Key changes: two "
            "  consistent board liaisons (rather than rotating), six "
            "  meetings/year cadence, narrowed audit-oversight scope to "
            "  *review and recommend approval* (rather than *review and "
            "  approval*).\n"
            "- **Policy 303.4 — Administrator Salary and Other "
            "  Compensation.** Adopted at the same May 26 meeting, after "
            "  sitting in committee since March.\n"
            "- **600-policy series** (curriculum / instruction). Adopted "
            "  at the [March 10 meeting](../meetings/2026/2026-03-10-regular-meeting-of-the-board-of-directors.md) "
            "  by a 5–2 vote — Directors Abraham and Finch voted no, "
            "  citing RAM class-size sizing concerns and impact on "
            "  teachers.\n\n"
            "## Tabled / in active review\n\n"
            "- **Policy 207 — Board of Directors Legal Counsel.** Tabled "
            "  at multiple meetings while the committee works out what "
            "  constitutes \"significant cost\" thresholds.\n"
            "- **Policy 303.2 — Administrator Qualifications, "
            "  Recruitment, and Appointment.** Tabled. This policy is "
            "  central to ongoing arguments about board involvement in "
            "  administrator hiring — see [Superintendent](superintendent.md). "
            "  Sticking point in committee: how many board members may "
            "  participate in interview committees, and at what "
            "  administrative levels (executive, executive director, "
            "  building-level).\n"
            "- **700-policy series — Noninstructional Operations & "
            "  Business Services.** Tabled at May 26 to incorporate 14 new "
            "  Policy Primers from the IASB and address fiscal-management "
            "  edits, internal-controls changes, and a three-year email-"
            "  retention provision.\n"
            "- **500-policy series — Students.** In active review (4 "
            "  meetings referenced in 2026).\n"
            "- **900-policy series — School District-Community "
            "  Relations.** Small edits to designate Deputy Superintendent "
            "  / Chief Operating Officer roles; under review.\n\n"
            "## Policy Primers (IASB)\n\n"
            "ICCSD receives Policy Primers from the Iowa Association of "
            "School Boards as state and federal regulations change. The "
            "May 26 P&G readout referenced **14 new primers** in the 700 "
            "series alone, which is why the series was tabled rather than "
            "rushed.\n"
        ),
        "questions": [
            "Which 700-series policies will land in the final adoption when "
            "the committee brings them back?",
            "How will Policy 303.2 (administrator hiring) be amended given "
            "the May 2026 leadership-transition context, and will it apply "
            "retroactively?",
            "What is the typical multi-reading timeline from first committee "
            "discussion to final board adoption?",
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
        "body": (
            "## Open enrollment in 2026\n\n"
            "Open-enrollment approvals appear on nearly every 2026 "
            "regular board meeting consent agenda — one or two batches "
            "per meeting covering both the in-progress school year "
            "(25-26) and the upcoming year (26-27). These are routine "
            "approvals of individual student transfer requests; the board "
            "does not typically discuss them on the record beyond the "
            "consent-agenda motion.\n\n"
            "Representative recent batches:\n\n"
            "- *5-26-2026 Board Meeting OE (25-26)* and *5-26-2026 Board "
            "  Meeting OE (26-27)* — adopted at the "
            "  [May 26, 2026 meeting](../meetings/2026/2026-05-26-regular-meeting-of-the-board-of-directors-amended-agenda.md) "
            "  as Consent Agenda item 7.\n"
            "- Similar batches appear in every prior 2026 regular meeting "
            "  on the [meeting index](../meetings/2026/index.md).\n\n"
            "## Attendance-area boundary changes\n\n"
            "**No district-wide attendance-area boundary changes have "
            "appeared on the 2026 board agendas reviewed.** Boundary "
            "shifts in ICCSD are rare events that typically require "
            "multi-meeting deliberation and community engagement, and "
            "none reached the public agenda during 2026.\n\n"
            "Several public commenters at recent meetings have raised "
            "**potential school closures** in connection with the "
            "district's [financial crisis](budget.md) — for example, the "
            "May 26 public-comment period included direct questions about "
            "how many schools might need to close. Those are speakers' "
            "framings of what may be coming, not formal board actions on "
            "the record yet.\n"
        ),
        "questions": [
            "When was the last district-wide attendance-area review, and "
            "what's the trigger threshold for the next one?",
            "If school closures do come onto the agenda as a financial-"
            "crisis response, what process will the board use, and what "
            "community engagement is required?",
            "What are the recent open-enrollment approval/denial rates, "
            "and which schools are net-receivers vs. net-senders?",
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
