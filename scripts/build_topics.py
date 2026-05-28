"""Auto-generate topic pages as fact dashboards.

Each topic page = stable intro (hand-written, lives in the TOPICS dict)
+ four auto-aggregated sections:

  1. 2026 meetings on this topic — meetings whose attachments matched.
  2. 2026 documents on this topic — direct deep-links to PDFs.
  3. 2026 press coverage on this topic — news articles matched by keyword.
  4. Open questions — hand-written, stable.

The page contains **no interpretive characterization added by the site**.
Auto-aggregated sections refresh every time the script runs — so when
the press file is updated, the topic pages reflect it the same day.
This script is called by refresh_press.py as part of the daily refresh.
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
        "_disabled_body": (
            "## The 2026 financial crisis — what actually happened\n\n"
            "ICCSD's 2026 has been dominated by an unfolding financial-"
            "management crisis whose origin event is now well-documented "
            "in the press. The story — drawn from the board record and "
            "the [2026 news coverage index](../press/2026.md):\n\n"
            "### Origin (August 2025)\n\n"
            "District administrators moved **$10 million from the "
            "health-insurance fund into the general fund** to cover a "
            "payroll cash-flow shortfall, **without notifying the board**. "
            "The transfer was then omitted from the next quarterly "
            "financial report — what district leaders later called "
            "*\"a mistake.\"*\n\n"
            "Internal context for how this became possible: Cedar Rapids "
            "Gazette emails show former CFO Leslie Finger (retired June "
            "2023) had warned his successor Adam Kurth about ~$500K in "
            "federal tax penalties, the absence of financial reports, "
            "and growth in the special-education deficit *\"by millions of "
            "dollars.\"* Between September 2023 and June 2025, ICCSD "
            "incurred **$525,110 in federal tax penalties** for filing "
            "payroll and excise taxes *\"significantly late.\"* Kurth left "
            "the district in November 2025.\n\n"
            "### January–March 2026 — the crisis emerges and the cuts grow\n\n"
            "- **January 27** — board learns about the $10M transfer at "
            "  its regular meeting. Directors are told the transfer hadn't "
            "  required board approval; an attorney later advises a review. "
            "  ([meeting](../meetings/2026/2026-01-27-regular-meeting-of-the-board-of-directors.md))\n"
            "- **January 30** — KCRG's Libbie Randall breaks the story "
            "  publicly. The board subsequently retroactively approves the "
            "  transfer.\n"
            "- **February 10** — FY26 Q2 Financial Report presented. "
            "  Payroll had been budgeted to rise 2–3%; **it rose 9%**, "
            "  putting ICCSD on pace to spend ~**$13.5 million over "
            "  budget**. Enrollment fell by 181 students (~1.25% of the "
            "  student body) FY25 → FY26.\n"
            "- **February 17** — FY2024-2028 Audit RFP recommendation "
            "  discussed at Board Work Session — first formal board "
            "  acknowledgment of the multi-year audit backlog. "
            "  ([meeting](../meetings/2026/2026-02-17-board-work-session-amended-agenda.md))\n"
            "- **February 24** — FY27 Certified Budget Update presented. "
            "  Same week, the Daily Iowan details the proposed cuts: "
            "  attrition-based teacher reductions, administrator "
            "  reassignments to building-level roles, bus-route "
            "  consolidation. Cut estimate by Feb 25: ~$8M.\n"
            "- **March 3** — Special board meeting authorizes **FY26 "
            "  Anticipatory Warrants** (short-term borrowing) and reviews "
            "  Budget Reduction Proposals. "
            "  ([meeting](../meetings/2026/2026-03-03-special-board-meeting-5-00-pm-amended-agenda.md))\n"
            "- **March 4** — *\"We don't have financials to present.\"* "
            "  Administrators tell directors at this meeting they cannot "
            "  present complete financial records. CBS2 reports monthly "
            "  expense and revenue tracking has been incomplete for nearly "
            "  three years.\n"
            "- **March 24** — **Board adopts $7.5M in FY26-27 cuts, "
            "  5–2.** Directors Finch and Lingo vote no. Same date hosts "
            "  the statutory public hearing on the FY27 property-tax levy. "
            "  ([meeting](../meetings/2026/2026-03-24-regular-meeting-board-of-directors-immediately-following-spe.md))\n\n"
            "### April 2026 — banks reject the loan, bond rating lost\n\n"
            "- **April 1** — Pat Moore announced as the new permanent CFO "
            "  (succeeding Interim CFO Kim Michael-Lee, who'd started Feb "
            "  25). Moore comes from Solon CSD where she'd been CFO since "
            "  2004.\n"
            "- **April 14** — Board approves Pat Moore's contract.\n"
            "- **April 28** — Board drops the $25M borrowing plan. "
            "  **Every bank the district approached rejected the loan**, "
            "  largely because ICCSD does not have up-to-date audits. "
            "  KCRG: ~$7.32M of debts come due within a month, and "
            "  *\"cash is so tight the district might not be able to meet "
            "  July's payroll if the district pays off its health "
            "  insurance loan before the next fiscal year.\"* Same meeting: "
            "  **ESC sold to the City of Iowa City for $3.2M.**\n"
            "- **May 1** — Bond rating loss confirmed; driven by missing "
            "  audits.\n\n"
            "### May 2026 — facilities plan paused, leadership transition\n\n"
            "- **May 12** — **$104M Facilities Master Plan paused** by "
            "  unanimous board vote. Public comment period sees multiple "
            "  community members call for replacement of *\"the current "
            "  superintendent, deputy superintendent and HR director.\"* "
            "  Board also discusses asking the state for permission to "
            "  raise spending authority; state takeover is on the table in "
            "  the worst case. "
            "  ([meeting](../meetings/2026/2026-05-12-regular-meeting-of-the-board-of-directors.md))\n"
            "- **May 23** — Superintendent Matt Degner publicly announces "
            "  his resignation by email and requests transition to "
            "  Executive Director of Secondary Schools.\n"
            "- **May 26** — Board approves Degner's transition 5–2 "
            "  (Finch, Lingo no). Three property-sale proceeds-deposit "
            "  resolutions adopted (Hills, ESC, Scanlon). New CFO Pat Moore "
            "  presents the audit catch-up plan: FY24 audit by July 2026, "
            "  FY25 by November 2026, FY26 by the March 31, 2027 statutory "
            "  deadline. "
            "  ([meeting](../meetings/2026/2026-05-26-regular-meeting-of-the-board-of-directors-amended-agenda.md) "
            "  · [watch the vote on YouTube](https://youtu.be/nMlbmq_NgoI?t=1757))\n\n"
            "### Audit backlog — who, when, why\n\n"
            "ICCSD has switched audit firms from **RSM Audit Services** to "
            "**Bohnsack & Frommelt LLP** for the FY24, FY25, and FY26 "
            "audits, with a commitment to complete all three no later than "
            "May 2027. Per the Cedar Rapids Gazette, Iowa school districts "
            "statewide are 1-2 years behind on audits due to a shortage of "
            "school auditors — but the ICCSD backlog cost the district its "
            "bond rating and access to bank financing.\n"
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
        "_disabled_body": (
            "## The 2026 transition\n\n"
            "Matt Degner is ICCSD's Superintendent of record going into "
            "2026 — recognized as a finalist for **National Superintendent "
            "of the Year** in the months before the financial crisis broke "
            "publicly. That national recognition became a recurring point "
            "of contrast in later 2026 community commentary. The year "
            "unfolded into a leadership transition closely intertwined "
            "with the district's [financial crisis](budget.md):\n\n"
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
            "  ([watch the vote on YouTube](https://youtu.be/nMlbmq_NgoI?t=1757))\n"
            "- **May 26, 2026 — Interim Superintendent search discussed.** "
            "  Grundmeier (the firm that conducted the recent CFO search) "
            "  presented three engagement levels — recruitment-only, "
            "  full-service interim search, or a combined interim + "
            "  permanent engagement. Board consensus: the interim should "
            "  not be eligible for the permanent role, and the permanent "
            "  search should be a separate engagement decision.\n\n"
            "## Public pressure for resignation\n\n"
            "At the **May 12, 2026 board meeting** — two weeks before "
            "Degner's resignation announcement — multiple community "
            "members called during public comment for the replacement of "
            "*\"the current superintendent, deputy superintendent and HR "
            "director.\"* (Per [CBS2](../press/2026.md#may-2026) and "
            "[KCRG](../press/2026.md#may-2026) coverage of that meeting.) "
            "Iowa City resident Maka Pilcher: *\"The remaining members, to "
            "the public's dismay, demonstrated a costly allegiance to the "
            "admin team whose mismanagement got us here.\"* ICCSD resident "
            "Robert Cargill: *\"The Iowa City Community School District "
            "board of education cannot move forward from this crisis with "
            "any credibility whatsoever without replacing the Iowa City "
            "Community School District superintendent and leadership "
            "team.\"*\n\n"
            "After Degner's May 23 email announcing his resignation and "
            "transition request, the May 26 meeting included roughly 30 "
            "minutes of public comment opposing the transition without an "
            "open search. Repeated themes from commenters (these are "
            "speakers' characterizations, not board findings):\n\n"
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
            "  page; [watch the May 26 public comment period on YouTube]"
            "(https://youtu.be/nMlbmq_NgoI) for the verbatim record.\n\n"
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
        "_disabled_body": (
            "## $104M Facilities Master Plan paused (May 12, 2026)\n\n"
            "At the [May 12, 2026 regular meeting](../meetings/2026/2026-05-12-regular-meeting-of-the-board-of-directors.md), "
            "the board unanimously adopted the **Facilities Master Plan "
            "Resolution**, temporarily pausing projects in the previously "
            "approved $104 million plan — including new athletic "
            "fieldhouses and the $14 million investment in the Coralville "
            "Recreation Center pool. Per [KCRG May 12](../press/2026.md#may-2026), "
            "the pause was part of the district's response to the "
            "[financial crisis](budget.md) and the inability to obtain "
            "external financing (the $25M loan request was rejected by "
            "every bank approached).\n\n"
            "## Three property sales in 2026\n\n"
            "ICCSD moved three district-owned properties through the "
            "statutory public-hearing-and-conveyance process during 2026, "
            "with the proceeds of each sale directed to the General Fund:\n\n"
            "- **Hills property** — 301 W. Main Street, Hills, Iowa. "
            "  Public hearing and proceeds-deposit resolution adopted at "
            "  the [May 26, 2026 board meeting](../meetings/2026/2026-05-26-regular-meeting-of-the-board-of-directors-amended-agenda.md).\n"
            "- **Educational Services Center (ESC)** — 1725 N. Dodge "
            "  Street, Iowa City. **Sold to the City of Iowa City for "
            "  $3.2 million** at the "
            "  [April 28 meeting](../meetings/2026/2026-04-28-regular-meeting-of-the-board-of-directors-amended-agenda.md). "
            "  The City announced May 13 that the building will become "
            "  the new Iowa City Police Department headquarters, target "
            "  move-in 2029. Proceeds-deposit resolution adopted at the "
            "  May 26 meeting.\n"
            "- **Scanlon parcel** — ~42.4 acres of unimproved real estate "
            "  previously purchased from Scanlon Family, L.L.C. Public "
            "  hearing and proceeds-deposit resolution adopted at the "
            "  May 26 meeting.\n\n"
            "All three sales were part of the year's larger response to "
            "the district's [unfolding financial-management crisis](budget.md).\n\n"
            "## $14M Coralville pool — four-option decision\n\n"
            "A proposed $14 million competition swimming pool in Coralville "
            "— part of the (now-paused) Master Facilities Plan, intended "
            "to give West High and Liberty High independent swim programs "
            "— remains under board consideration. Per KCRG (April 29) and "
            "CBS2 (May 12), the board is weighing four options: (1) direct "
            "contribution to design and construction, (2) sign a long-term "
            "lease with annual payments, (3) build a district natatorium, "
            "(4) rent local facilities for practices and meets. The "
            "Coralville City Administrator confirmed a meeting with Degner "
            "and that the city is gathering pricing through May.\n\n"
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
        "_disabled_body": (
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
        "_disabled_body": (
            "## School closures and elementary reconfiguration\n\n"
            "In **March 2026**, the district's financial consultant **PFM** "
            "formally recommended that ICCSD evaluate closing or "
            "consolidating school buildings as part of its long-term "
            "cost-reduction strategy in response to the "
            "[financial crisis](budget.md). (Per the [Cedar Rapids Gazette](../press/2026.md#march-2026) "
            "and [CBS2 Iowa](../press/2026.md#march-2026).)\n\n"
            "That recommendation triggered an **elementary reconfiguration** "
            "discussion — restructuring grade levels and attendance "
            "patterns across elementary schools — which the board took up "
            "at a special meeting later in the spring. No formal closure "
            "decision has been adopted as of the May meetings.\n\n"
            "At the May 12 board meeting, public commenters raised the "
            "prospect of school closures and pressed the board for "
            "transparency about which schools might be affected. The "
            "district has committed to community engagement before any "
            "formal closure decision.\n\n"
            "## Open enrollment in 2026\n\n"
            "Open-enrollment approvals appear on nearly every 2026 "
            "regular board meeting consent agenda — one or two batches "
            "per meeting covering both the in-progress school year "
            "(25-26) and the upcoming year (26-27). These are routine "
            "approvals of individual student transfer requests; the board "
            "does not typically discuss them on the record beyond the "
            "consent-agenda motion.\n\n"
            "Enrollment context: per the FY26 Q2 Financial Report and "
            "subsequent press coverage, ICCSD enrollment fell by **181 "
            "students (~1.25%)** between FY25 and FY26. Iowa Public "
            "Radio's spring 2026 NPR series featured ICCSD as a case study "
            "in how Iowa's universal Education Savings Account (ESA) "
            "program has accelerated enrollment loss in urban public "
            "districts.\n\n"
            "## Attendance-area boundary changes\n\n"
            "**No district-wide attendance-area boundary changes have "
            "been adopted on the 2026 board agendas reviewed.** Boundary "
            "shifts in ICCSD are rare events that typically require "
            "multi-meeting deliberation and community engagement, and "
            "none reached final action during 2026 — though the school-"
            "closure / reconfiguration discussion above functionally "
            "raises the same set of questions.\n"
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


# --- press article parsing (shared structure with build_timeline.py) ---

_H3_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
_PRESS_META_RE = re.compile(
    r"^\*\*([^*]+?)\*\*\s*(?:—\s*([^—\n]+?))?\s*(?:—\s*\*([^*]+?)\*)?\s*$"
)


def parse_press_articles_for_topics(press_md: str) -> list[dict]:
    """Return a flat list of press articles with headline/publication/date/url.

    Format mirrors what build_timeline.py extracts so the two stay
    consistent. Each topic page filters this list by keyword match.
    """
    articles: list[dict] = []
    lines = press_md.splitlines()
    i = 0
    while i < len(lines):
        m_h3 = _H3_RE.match(lines[i])
        if not m_h3:
            i += 1
            continue
        headline = m_h3.group(1).strip().strip('"')
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
        articles.append({
            "headline": headline,
            "publication": publication,
            "date": date_str,
            "url": url,
        })
        i += 1
    return articles


def match_articles_to_topic(articles: list[dict], keywords: list[str]) -> list[dict]:
    """Filter to articles whose headline contains any of the keywords."""
    out: list[dict] = []
    for a in articles:
        kws = matches(a["headline"], keywords)
        if kws:
            out.append({**a, "matched_keywords": kws})
    return out


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
                     press_articles: list[dict],
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
    # NOTE: `body` field is intentionally not rendered. Earlier versions of
    # this generator included hand-written narrative bodies; those have
    # been retired in favor of fact-dashboard sections only. See repo
    # README for the rationale (the site auto-maintains and shouldn't
    # parrot one source's framing).
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

    # --- press coverage section (auto, refreshes daily) ---
    matched_articles = match_articles_to_topic(press_articles, spec["keywords"])
    lines.extend([
        "",
        "## 2026 press coverage on this topic",
        "",
    ])
    if not matched_articles:
        lines.append(
            "_No 2026 press articles matched the keyword set yet. New "
            "coverage is picked up here automatically as the [press "
            "index](../press/2026.md) is refreshed._"
        )
    else:
        lines.append(
            f"Articles matched by keyword from the [press index](../press/2026.md). "
            f"{len(matched_articles)} article{'s' if len(matched_articles) != 1 else ''} "
            f"matched. The headline and publication are the source's own; "
            f"the site adds no characterization."
        )
        lines.append("")
        for a in matched_articles:
            pub = a.get("publication", "") or "(publication unknown)"
            date = a.get("date", "") or ""
            url = a.get("url", "")
            display = f"\"{a['headline']}\""
            line = f"- **{date or '—'}** — *{pub}* — {display}"
            if url:
                line += f" — [read article]({url})"
            lines.append(line)

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
        f"*All lists on this page are derived automatically by keyword match "
        f"against the [2026 attachment index]"
        f"(https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/data/attachments_2026.json) "
        f"and the [press index](../press/2026.md). They refresh whenever the "
        f"press file is updated. The site adds no characterization of its own — "
        f"each entry shows the source's wording with the source's citation.*",
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
    ap.add_argument("--press", type=Path, default=None,
                    help="Optional path to docs/press/<year>.md. When "
                         "provided, each topic page gets a 'press coverage' "
                         "section listing matched articles.")
    ap.add_argument("--out", type=Path, required=True, help="docs/topics/")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    with open(args.attachments, encoding="utf-8") as f:
        data = json.load(f)

    press_articles: list[dict] = []
    if args.press and args.press.exists():
        press_articles = parse_press_articles_for_topics(
            args.press.read_text(encoding="utf-8")
        )
        print(f"Loaded {len(press_articles)} press articles for matching.")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    build_topics_index(args.out)
    for slug, spec in TOPICS.items():
        page = build_topic_page(slug, spec, data, press_articles, generated_at)
        (args.out / f"{slug}.md").write_text(page, encoding="utf-8")
        print(f"Wrote {args.out / (slug + '.md')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
