"""Generate MkDocs meeting pages from scraped ICCSD agenda content + AID index.

Inputs:
  - --source-root <path>: ICCSD/<YEAR>/ folder on disk. Each meeting lives
    under a meeting-type subfolder (Board of Directors General Meeting,
    Committee Meeting, etc.) as a folder containing agenda.md +
    meeting.json + attachments/ + (sometimes) transcript.json.
  - --attachments <path>: data/attachments_<year>.json from extract_aids.py.
  - --meetings-json <path>: ICCSD/all_meetings.json (for type + canonical
    DateTime).
  - --year <int>
  - --out <path>: docs/meetings/<year>/ — pages and index land here.

For each meeting that has BOTH a local agenda.md AND an entry in the
attachments JSON, the script:
  1. Reads agenda.md
  2. Replaces every `[label](attachments/local.pdf)` link with the direct
     district URL (https://simbli.eboardsolutions.com/Meetings/Attachment.aspx?S=...&AID=...&MID=...)
     by matching `label` against the AID JSON's `title` field.
  3. Wraps in MkDocs frontmatter (title, date)
  4. Appends a metadata footer with source URL and generation timestamp
  5. Writes to docs/meetings/<year>/<YYYY-MM-DD>-<slug>.md

For meetings present in the AID JSON but missing on disk, a stub page is
written linking to the district URL only.

Then writes docs/meetings/<year>/index.md grouping meetings by month.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote


# Site URL — embedded in the AI prompts below so the tool fetches the
# right page directly from GitHub Pages.
SITE_URL = "https://b00mhauer.github.io/iowa-city-schools-board-archive"


def _ai_buttons(prompt: str) -> str:
    """Render a one-line 'Ask AI' button block with ChatGPT / Gemini /
    Perplexity links, each pre-loaded with `prompt`.

    The buttons just open each tool's web app with the prompt already
    typed into the chat box (via the `?q=` query parameter). The user
    hits enter; the tool fetches the URL embedded in the prompt and
    answers from it. No backend required.
    """
    q = quote(prompt, safe="")
    return (
        f"[Ask ChatGPT](https://chatgpt.com/?q={q})"
        f" &nbsp;·&nbsp; "
        f"[Ask Gemini](https://gemini.google.com/app?q={q})"
        f" &nbsp;·&nbsp; "
        f"[Ask Perplexity](https://www.perplexity.ai/?q={q})"
    )


# --- helpers ---

_SLUG_BAD = re.compile(r"[^a-z0-9]+")


def slugify(s: str, max_len: int = 60) -> str:
    s = s.lower()
    s = _SLUG_BAD.sub("-", s).strip("-")
    return s[:max_len].rstrip("-") or "meeting"


def parse_title_dt(title_dt: str) -> tuple[str, str] | None:
    """Parse '05/26/2026 - 06:00 PM' -> ('2026-05-26', '06:00 PM')."""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})\s*-\s*(.*)", title_dt or "")
    if not m:
        return None
    mm, dd, yy, time = m.groups()
    return f"{yy}-{int(mm):02d}-{int(dd):02d}", time.strip()


def load_json(p: Path) -> Any:
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# --- attachment URL rewriting ---

# Regex captures: `[link text](attachments/local-filename.ext)` plus an
# optional trailing " — N,NNN bytes". We drop the byte count for the
# public page.
#
# Quirks the regex has to tolerate:
#   - `[...]` inside the link LABEL (e.g. `IowaSDPA[25]Accredible...`) →
#     non-greedy `(.+?)` finds the right closing `]`.
#   - `(...)` inside the URL (e.g. `BoardReport (2)5.12.26.pdf` or
#     `Iowa City Schools (IA) - Internet Services (Rene.pdf` where the
#     second paren is unbalanced because the filename was truncated to
#     fit Windows path limits) → handled by non-greedy URL match anchored
#     to end-of-line. Each attachment line in the agenda is self-
#     contained, so EOL is a reliable terminator that balanced-paren
#     counting can't be (because unbalanced parens happen in real data).
ATT_LINK_RE = re.compile(
    r"\[(.+?)\]\(attachments/.+?\)(\s*—\s*[\d,]+\s*bytes)?$",
    re.MULTILINE,
)

# A line consisting solely of a bold label like `**Recommendation**` or
# `**Supporting Documents:**`. The agenda source puts content on the very
# next line, with no blank between — markdown then collapses label +
# content into one visual paragraph. We insert a blank to split them.
BOLD_LABEL_LINE_RE = re.compile(r"^\s*\*\*[^*\n]+\*\*\s*:?\s*$")


def normalize_label_blocks(md: str) -> str:
    """Convert standalone bold-label lines into small uppercase labels.

    The district's agenda format emits structural labels as bold lines:
        **Recommendation**
        Motion to approve...

    Two problems with that:
      1. Markdown collapses the single newline → "Recommendation Motion
         to approve...".
      2. Even rendered with a blank line, bold competes with the section
         headings for visual weight.

    We rewrite each such line to:
        <p class="agenda-label">Recommendation</p>

        Motion to approve...

    where `.agenda-label` is styled (in extra.css) as a small uppercase
    tag — quieter than bold, but still clearly delineating the field.
    """
    lines = md.splitlines()
    out: list[str] = []
    for i, line in enumerate(lines):
        if BOLD_LABEL_LINE_RE.match(line):
            # Strip leading whitespace, ** wrappers, and any trailing ":"
            # (the district sometimes writes `**Supporting Documents:**`
            # — colon is inside the bold). The CSS handles separator
            # styling so the colon would just be noise.
            inner = line.strip().strip("*").rstrip(":").strip()
            out.append(f'<p class="agenda-label">{inner}</p>')
            if i + 1 < len(lines) and lines[i + 1].strip() != "":
                out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def normalize_title(t: str) -> str:
    """Aggressive normalization for fuzzy title matching."""
    return re.sub(r"[^a-z0-9]+", "", t.lower())


def rewrite_attachments(md: str, attachments: list[dict], mid: int) -> tuple[str, int, int]:
    """Replace local attachment links with direct district URLs.

    Returns (new_md, replaced_count, missed_count).
    """
    # Index attachments two ways: by exact title and by normalized title.
    by_title: dict[str, dict] = {}
    by_norm: dict[str, list[dict]] = {}
    for a in attachments:
        by_title.setdefault(a["title"], a)
        by_norm.setdefault(normalize_title(a["title"]), []).append(a)

    # Track which AIDs we've already linked so duplicates in the agenda map
    # to subsequent same-titled attachments (rare but happens).
    consumed: set[int] = set()

    replaced = 0
    missed = 0

    def find_match(label: str) -> dict | None:
        # 1. exact title match, prefer unconsumed
        if label in by_title and by_title[label]["aid"] not in consumed:
            return by_title[label]
        # 2. normalized match
        norm = normalize_title(label)
        for cand in by_norm.get(norm, []):
            if cand["aid"] not in consumed:
                return cand
        # 3. any AID at all with this normalized title (allow duplicate link)
        if norm in by_norm:
            return by_norm[norm][0]
        return None

    def repl(match: re.Match) -> str:
        nonlocal replaced, missed
        label = match.group(1)
        att = find_match(label)
        if att is None:
            missed += 1
            return f"[{label}]({_district_meeting_url(mid)}) _(see meeting page on district site)_"
        consumed.add(att["aid"])
        replaced += 1
        return f"[{label}]({att['url']})"

    new_md = ATT_LINK_RE.sub(repl, md)
    return new_md, replaced, missed


def _district_meeting_url(mid: int) -> str:
    return f"https://simbli.eboardsolutions.com/SB_Meetings/ViewMeeting.aspx?S=36031992&MID={mid}"


# --- page generation ---


def transform_agenda(md_in: str, meeting_record: dict, mid: int) -> tuple[str, dict]:
    """Take an existing agenda.md and produce the public meeting page body.

    Steps:
      - drop the original first-line H1 (we put title in frontmatter)
      - drop the original metadata block (Date/Location/Source)
      - drop the leading '---' divider
      - rewrite attachment links
      - return (body, stats)
    """
    lines = md_in.splitlines()
    # Drop H1 and the metadata block until and including the first '---' line.
    body_start = 0
    saw_divider = False
    for i, ln in enumerate(lines):
        if ln.strip() == "---":
            body_start = i + 1
            saw_divider = True
            break
    if not saw_divider:
        # Fall back: skip the title line if it's an H1
        if lines and lines[0].startswith("# "):
            body_start = 1

    body = "\n".join(lines[body_start:]).lstrip("\n")
    body, replaced, missed = rewrite_attachments(body, meeting_record["attachments"], mid)
    body = normalize_label_blocks(body)
    return body, {"replaced": replaced, "missed": missed}


def _youtube_url_for(corpus_root: Path, date_str: str, slug: str) -> str | None:
    """If a transcript exists in /corpus/ for this meeting, return the
    YouTube video URL from its meta block. Raw transcripts are not
    published as web pages (too noisy for human reading) — but the
    YouTube link itself is useful on the meeting page so a reader can
    watch the recording directly.
    """
    candidate = corpus_root / "transcripts" / "2026" / f"{date_str}-{slug}.md"
    if not candidate.exists():
        return None
    try:
        for line in candidate.read_text(encoding="utf-8").splitlines():
            # Format: **Video:** [Title](https://www.youtube.com/watch?v=...)
            if line.startswith("**Video:**"):
                m = re.search(r"\((https?://[^\s)]+)\)", line)
                if m:
                    return m.group(1)
    except Exception:
        return None
    return None


def load_summaries(path: Path) -> dict[int, str]:
    """Load editorial summaries keyed by MID from a JSON sidecar.

    Format: {"<mid>": "markdown body string"}

    Allows curated 'What happened' summaries to be added to individual
    meeting pages without modifying the generator. Missing file or
    missing MID is fine — page just renders without a summary section.
    """
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items() if v}


def render_supporting_docs(attachments: list[dict]) -> str:
    """Render the supporting-documents list grouped by agenda item.

    Each attachment record has `section` (e.g. "E.01"), `item_title`
    (e.g. "1. Resolution on the Proposed Deposit..."), `title` (the
    document's own title), and `url` (the direct district deep-link).

    We group by section.item_title — items with multiple attached PDFs
    show as a single subsection with a bulleted list; single-attachment
    items still render as a labeled subsection so the agenda context is
    preserved.
    """
    if not attachments:
        return ""

    # Sort by section then by an implicit attachment order
    sorted_atts = sorted(attachments, key=lambda a: (a.get("section", ""),))

    # Group by (section, item_title) tuple, preserving order
    groups: list[tuple[str, str, list[dict]]] = []
    by_key: dict[tuple[str, str], list[dict]] = {}
    for a in sorted_atts:
        key = (a.get("section", ""), a.get("item_title", "") or "(no item title)")
        if key not in by_key:
            by_key[key] = []
            groups.append((key[0], key[1], by_key[key]))
        by_key[key].append(a)

    out = ["## Supporting documents", ""]
    out.append(
        f"{len(attachments)} document"
        f"{'s' if len(attachments) != 1 else ''} attached to this meeting on "
        f"the district portal, grouped by agenda item. Click any title to "
        f"open the PDF directly."
    )
    out.append("")
    for section, item_title, atts in groups:
        # Trim leading numbers/punctuation from item title for cleaner display
        clean_title = re.sub(r"^\s*\d+\.?\s*", "", item_title).strip()
        if not clean_title:
            clean_title = item_title
        out.append(f"### {clean_title}")
        out.append("")
        for a in atts:
            out.append(f"- [{a['title']}]({a['url']})")
        out.append("")
    return "\n".join(out)


def render_meeting_page(meeting_record: dict, agenda_md: str | None,
                        meeting_type: str, generated_at: str,
                        out_dir: Path, slug: str,
                        corpus_root: Path,
                        summary: str | None = None) -> tuple[str, dict]:
    """Compose the full markdown page for one meeting.

    Page body for a meeting:
      1. Frontmatter
      2. H1 title
      3. Metadata card (date, type, source URL)
      4. "What happened" editorial summary if curated
      5. Watch & read on source — YouTube + district portal links
      6. Supporting documents grouped by agenda item
      7. About-this-page footer

    The verbose section-by-section agenda body is intentionally NOT
    included here — readers who want the district's own agenda follow
    the portal link in step 5. The agenda markdown is preserved in
    /corpus/agendas/ for AI ingestion.
    """
    mid = meeting_record["mid"]
    title = meeting_record["title"]
    title_dt = meeting_record["title_datetime"]
    parsed = parse_title_dt(title_dt)
    date_str = parsed[0] if parsed else "unknown"
    time_str = parsed[1] if parsed else ""

    front_lines = [
        "---",
        f"title: {json.dumps(title)}",
        f"date: {date_str}",
        f"meeting_type: {json.dumps(meeting_type)}",
        f"mid: {mid}",
        "---",
        "",
        f"# {title}",
        "",
    ]

    # Wrap the metadata header in a styled div so CSS can dampen its
    # visual weight relative to the section headings. The `markdown`
    # attribute (md_in_html extension) tells the renderer to still
    # process bold + link inside.
    header = []
    header.append('<div class="meeting-meta" markdown>')
    header.append("")
    header.append(
        f"**Date / Time:** {date_str}"
        + (f" — {time_str}" if time_str else "")
    )
    header.append("")
    header.append(f"**Meeting Type:** {meeting_type}")
    header.append("")
    header.append(
        f"**Official agenda on district site:** "
        f"[Simbli eBoard meeting page]({meeting_record['source_url']})"
    )
    header.append("")
    header.append("</div>")
    header.append("")

    # Editorial summary block — only present if a curator wrote one for
    # this meeting (lives in data/summaries_<year>.json).
    if summary:
        header.append("## What happened")
        header.append("")
        header.append(summary.rstrip())
        header.append("")
        header.append("---")
        header.append("")

    # External links: watch the meeting on YouTube + full agenda on the
    # district portal. We don't republish transcripts or PDF text on the
    # website — those are too noisy to serve as human content. They live
    # in /corpus/ for AI ingestion.
    yt_url = _youtube_url_for(corpus_root, date_str, slug)
    if yt_url:
        header.append("## Watch / read on source")
        header.append("")
        header.append(
            f"- **[Watch the meeting on YouTube]({yt_url})** — auto-captions "
            f"available; the meeting is the source of truth, not any "
            f"transcript of it."
        )
        header.append(
            f"- **[Full agenda + supporting documents on the district portal]"
            f"({meeting_record['source_url']})** — every attached PDF lives "
            f"there. Direct deep-links to specific documents are listed on "
            f"this page below."
        )
        header.append("")
        header.append("---")
        header.append("")

    # Ask AI block — clicking opens ChatGPT / Gemini / Perplexity with a
    # question about this meeting pre-loaded. The AI fetches this page
    # (which is on the public site) and answers from it.
    meeting_page_url = f"{SITE_URL}/meetings/{date_str[:4]}/{date_str}-{slug}/"
    ai_prompt = (
        f"Read this ICCSD Board of Directors meeting summary and supporting "
        f"document list, then answer my questions about it. Start with a "
        f"~150-word overview: what happened, who voted how on any contested "
        f"items, and what's still unresolved. The page is at {meeting_page_url}"
    )
    header.append("## Ask an AI about this meeting")
    header.append("")
    header.append(
        "These open an AI chat with a question about this meeting pre-loaded. "
        "Just click and hit enter."
    )
    header.append("")
    header.append(_ai_buttons(ai_prompt))
    header.append("")
    header.append("---")
    header.append("")

    # The agenda body itself is no longer published on the website — it
    # was a verbose district-formatted document that read as a dump
    # rather than a synthesized page. Readers who want it follow the
    # "Full agenda on district portal" link above. (The agenda markdown
    # is preserved in /corpus/agendas/ for AI ingestion.)
    stats = {"replaced": 0, "missed": 0}
    body = render_supporting_docs(meeting_record.get("attachments", []))
    if not body:
        body = (
            "_No supporting documents were attached to this meeting on "
            "the district portal. See the official meeting page for any "
            "minutes or motions published after the fact._"
        )

    footer_lines = [
        "",
        "---",
        "",
        "## About this page",
        "",
        f"Agenda content carried through from the district's published "
        f"materials for [MID {mid}]({meeting_record['source_url']}). Every "
        f"attachment link above points directly to the original PDF on the "
        f"district's Simbli eBoardSolutions portal — this archive does not "
        f"host the underlying files.",
        "",
        f"Captured by the [archive page generator]"
        f"(https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/scripts/build_pages.py) "
        f"on {generated_at}.",
        "",
        "Spot something wrong? Open an [issue]"
        "(https://github.com/b00mhauer/iowa-city-schools-board-archive/issues) — see "
        "[Methodology](../../methodology.md) for the editorial standard.",
        "",
    ]

    full = "\n".join(front_lines) + "\n".join(header) + body.rstrip() + "\n" + "\n".join(footer_lines)
    return full, stats


def _stub_body(meeting_record: dict) -> str:
    if not meeting_record["attachments"]:
        return (
            "_No supporting documents were attached to this meeting on the "
            "district portal. See the official meeting page for any motions "
            "or minutes published after the fact._\n"
        )
    lines = [
        "_Detailed agenda content is not currently available in this archive "
        "for this meeting. The list below is the full set of supporting "
        "documents from the district portal._",
        "",
        "## Supporting Documents",
        "",
    ]
    for att in meeting_record["attachments"]:
        lines.append(f"- [{att['title']}]({att['url']}) — {att['section']}: {att['item_title']}")
    lines.append("")
    return "\n".join(lines)


# --- discovery on disk ---


def find_local_meetings(source_root: Path) -> dict[int, dict]:
    """Walk YEAR/*/MEETING_FOLDER/meeting.json and index by MID."""
    out: dict[int, dict] = {}
    for meeting_json in source_root.rglob("meeting.json"):
        try:
            data = load_json(meeting_json)
        except Exception:
            continue
        mid = data.get("ID")
        if not isinstance(mid, int):
            continue
        agenda = meeting_json.parent / "agenda.md"
        if not agenda.exists():
            continue
        # Skip system folders / non-meeting JSONs
        out[mid] = {
            "agenda_path": agenda,
            "folder": meeting_json.parent,
            "meeting_json": data,
        }
    return out


def index_meeting_types(all_meetings: list[dict]) -> dict[int, str]:
    return {m["MID"]: m.get("Type", "") for m in all_meetings if isinstance(m.get("MID"), int)}


# --- index page ---


def write_index(out_dir: Path, year: int, pages: list[dict]) -> None:
    """Group meetings by month and emit docs/meetings/<year>/index.md.

    Sorted newest first — readers want the most recent meeting at the top.
    """
    pages_sorted = sorted(pages, key=lambda p: (p["date"], p["title"]),
                          reverse=True)

    months_by_num = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }

    lines = [
        f"# {year} Meetings",
        "",
        f"All public ICCSD Board of Directors meetings in {year}. Each link "
        f"opens the meeting page on this archive; the meeting page in turn "
        f"links to the official agenda and supporting documents on the "
        f"[district's portal](https://simbli.eboardsolutions.com/).",
        "",
        f"**{len(pages_sorted)} meetings** indexed for {year}.",
        "",
    ]

    current_month = None
    for p in pages_sorted:
        # date is YYYY-MM-DD
        try:
            month_num = int(p["date"].split("-")[1])
        except (IndexError, ValueError):
            month_num = 0
        if month_num != current_month:
            if current_month is not None:
                lines.append("")
            current_month = month_num
            month_name = months_by_num.get(month_num, "Unknown")
            lines.append(f"## {month_name} {year}")
            lines.append("")
        n_atts = p["attachment_count"]
        atts_label = (
            f" — {n_atts} doc{'s' if n_atts != 1 else ''}" if n_atts else ""
        )
        lines.append(
            f"- **{p['date']}** — [{p['title']}]({p['filename']})"
            f" *({p['meeting_type']})*{atts_label}"
        )
    lines.append("")

    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


# --- driver ---


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source-root", type=Path, required=True,
                    help="ICCSD/<YEAR>/ folder containing per-meeting subfolders")
    ap.add_argument("--attachments", type=Path, required=True,
                    help="data/attachments_<year>.json")
    ap.add_argument("--meetings-json", type=Path, required=True,
                    help="ICCSD/all_meetings.json")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True,
                    help="Output dir docs/meetings/<year>/")
    ap.add_argument("--summaries", type=Path, default=None,
                    help="Optional path to data/summaries_<year>.json")
    ap.add_argument("--corpus-root", type=Path, default=None,
                    help="Path to the /corpus/ directory (used to detect "
                         "transcripts so the YouTube link can be surfaced).")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    # Mirror agenda.md content into /corpus/agendas/ so it's preserved
    # in the repo for AI ingestion even though it's no longer on the site.
    corpus_root = args.corpus_root or Path("corpus")
    agendas_corpus = corpus_root / "agendas" / str(args.year)
    agendas_corpus.mkdir(parents=True, exist_ok=True)

    attachments_data = load_json(args.attachments)
    all_meetings = load_json(args.meetings_json)
    types_by_mid = index_meeting_types(all_meetings)
    summaries_by_mid = load_summaries(args.summaries) if args.summaries else {}
    if summaries_by_mid:
        print(f"Loaded {len(summaries_by_mid)} editorial summaries.")

    local = find_local_meetings(args.source_root)
    print(f"Found {len(local)} local meeting folders with agenda.md.")
    print(f"Found {len(attachments_data)} MIDs in attachments JSON.")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    pages: list[dict] = []
    seen_filenames: set[str] = set()
    total_replaced = total_missed = 0

    for mid_str, rec in attachments_data.items():
        mid = int(mid_str)
        parsed = parse_title_dt(rec["title_datetime"])
        if not parsed:
            print(f"  skip MID {mid}: bad TitleDateTime {rec['title_datetime']!r}",
                  file=sys.stderr)
            continue
        date_str, _ = parsed

        meeting_type = types_by_mid.get(mid, "Meeting")

        local_entry = local.get(mid)
        agenda_md = (
            local_entry["agenda_path"].read_text(encoding="utf-8")
            if local_entry else None
        )
        # Mirror raw agenda content to corpus (AI ingestion); not used
        # by the rendered page itself.
        if agenda_md is not None:
            agenda_corpus_path = agendas_corpus / f"{date_str}-{slugify(rec['title'])}.md"
            agenda_corpus_path.write_text(agenda_md, encoding="utf-8")

        slug = slugify(rec["title"])
        page_md, stats = render_meeting_page(
            rec, agenda_md, meeting_type, generated_at, args.out, slug,
            corpus_root=args.corpus_root or Path("corpus"),
            summary=summaries_by_mid.get(mid),
        )
        total_replaced += stats["replaced"]
        total_missed += stats["missed"]

        # (slug already computed above for transcript/extracts lookup)
        filename = f"{date_str}-{slug}.md"
        # Disambiguate if same date+title appears twice (e.g. closed session
        # immediately following a regular meeting)
        suffix = 2
        while filename in seen_filenames:
            filename = f"{date_str}-{slug}-{suffix}.md"
            suffix += 1
        seen_filenames.add(filename)

        (args.out / filename).write_text(page_md, encoding="utf-8")

        pages.append({
            "date": date_str,
            "title": rec["title"],
            "filename": filename,
            "meeting_type": meeting_type,
            "attachment_count": len(rec["attachments"]),
            "has_local": local_entry is not None,
        })

    write_index(args.out, args.year, pages)

    on_disk = sum(1 for p in pages if p["has_local"])
    stub = len(pages) - on_disk
    print(f"\nWrote {len(pages)} meeting pages to {args.out}")
    print(f"  {on_disk} with full agenda from disk")
    print(f"  {stub} as stubs (no local agenda.md)")
    print(f"  {total_replaced} attachment links rewritten to direct district URLs")
    if total_missed:
        print(f"  {total_missed} attachment links could not be matched "
              f"(fell back to meeting-page link)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
