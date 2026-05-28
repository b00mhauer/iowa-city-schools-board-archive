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

# Regex captures: `[link text](attachments/local-filename.ext)`
# Optional suffix: " — N,NNN bytes" — we drop this for the public page.
# `.+?` (non-greedy) lets us tolerate `[...]` inside the link label, which
# does happen (e.g. `IowaSDPA[25]Accredible...`). The trailing literals
# `\]\(attachments/` and `\)` anchor the match.
ATT_LINK_RE = re.compile(
    r"\[(.+?)\]\(attachments/[^)]+\)(\s*—\s*[\d,]+\s*bytes)?",
)


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
    return body, {"replaced": replaced, "missed": missed}


def render_meeting_page(meeting_record: dict, agenda_md: str | None,
                        meeting_type: str, generated_at: str) -> tuple[str, dict]:
    """Compose the full markdown page for one meeting."""
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

    header = []
    header.append(f"**Date / Time:** {date_str}" + (f" — {time_str}" if time_str else ""))
    header.append("")
    header.append(f"**Meeting Type:** {meeting_type}")
    header.append("")
    header.append(
        f"**Official agenda on district site:** "
        f"[Simbli eBoard meeting page]({meeting_record['source_url']})"
    )
    header.append("")
    header.append("---")
    header.append("")

    stats = {"replaced": 0, "missed": 0}
    if agenda_md is not None:
        body, stats = transform_agenda(agenda_md, meeting_record, mid)
    else:
        body = _stub_body(meeting_record)

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
    """Group meetings by month and emit docs/meetings/<year>/index.md."""
    pages_sorted = sorted(pages, key=lambda p: (p["date"], p["title"]))

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
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    attachments_data = load_json(args.attachments)
    all_meetings = load_json(args.meetings_json)
    types_by_mid = index_meeting_types(all_meetings)

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

        page_md, stats = render_meeting_page(rec, agenda_md, meeting_type, generated_at)
        total_replaced += stats["replaced"]
        total_missed += stats["missed"]

        slug = slugify(rec["title"])
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
