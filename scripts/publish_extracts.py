"""Publish PDF text extractions from the source folder into the repo.

The source ICCSD folder has `.txt` files (one per PDF attachment, produced
by an earlier text-extraction pass over the scraped PDFs). They are not
in the published repo by default — this script copies them into

    docs/meetings/<year>/text/<mid>/<attachment-slug>.md

with markdown frontmatter linking back to the source PDF on the district
portal and to the meeting page where the attachment appears.

Goal: make the corpus AI-scannable and search-indexable without forcing
readers to download every PDF. The original PDFs remain the source of
truth; these text extracts are explicitly flagged as machine-extracted.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


_SLUG_BAD = re.compile(r"[^a-z0-9]+")
_SAFE_FN = re.compile(r"[^A-Za-z0-9._-]+")


def slugify(s: str, max_len: int = 60) -> str:
    s = s.lower()
    s = _SLUG_BAD.sub("-", s).strip("-")
    return s[:max_len].rstrip("-") or "meeting"


def safe_filename(s: str, max_len: int = 80) -> str:
    """Filesystem-safe name for the extract file."""
    s = _SAFE_FN.sub("_", s).strip("_")
    return s[:max_len].rstrip("_") or "extract"


def parse_date(title_dt: str) -> str:
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", title_dt or "")
    if not m:
        return ""
    mm, dd, yy = m.groups()
    return f"{yy}-{int(mm):02d}-{int(dd):02d}"


def find_meetings_with_extracts(source_root: Path) -> list[Path]:
    out: list[Path] = []
    for p in source_root.rglob("meeting.json"):
        if (p.parent / "attachments").exists():
            out.append(p.parent)
    return out


def load_aid_lookup(attachments_json: Path) -> dict[int, dict]:
    """{mid: meeting_record} for direct-URL lookup."""
    data = json.loads(attachments_json.read_text(encoding="utf-8"))
    return {int(k): v for k, v in data.items()}


def find_aid_for_file(meeting_record: dict, file_stem: str) -> dict | None:
    """Find the AID record matching a local file by section prefix + title.

    Local filename pattern (from download_meeting.py):
        {SECTION}_{NN}_{sub_idx}_{sanitized stem}.{ext}
    e.g.  E_01_01_Affidavit of Publication - Deposit of Funds

    The AID JSON has `section` like "E.01" and `title` (original title).
    Matching strategy: extract section from local prefix, walk JSON
    attachments for that section in order; positional match works because
    both code paths walk the same tree.
    """
    m = re.match(r"^([A-Z])_(\d+)_(\d+)_(.*)$", file_stem)
    if not m:
        return None
    section_letter, section_num, sub_idx, stem_remaining = m.groups()
    target_section = f"{section_letter}.{int(section_num):02d}"
    sub_n = int(sub_idx)
    # Filter attachments for this section, take the Nth (1-indexed sub_idx)
    section_atts = [a for a in meeting_record["attachments"]
                    if a["section"] == target_section]
    if 1 <= sub_n <= len(section_atts):
        return section_atts[sub_n - 1]
    return None


def render_extract(text: str, source_pdf_url: str | None, attachment_title: str,
                   meeting_title: str, meeting_date: str, meeting_page: str,
                   mid: int, section: str | None) -> str:
    """Wrap raw extracted text in markdown with metadata header."""
    out: list[str] = []
    out.append("---")
    out.append(f"title: {json.dumps(attachment_title)}")
    out.append("---")
    out.append("")
    out.append(f"# {attachment_title}")
    out.append("")
    out.append('<div class="meeting-meta" markdown>')
    out.append("")
    out.append(f"**Meeting:** [{meeting_title}]({meeting_page}) — {meeting_date}")
    out.append("")
    if section:
        out.append(f"**Agenda section:** {section}")
        out.append("")
    if source_pdf_url:
        out.append(f"**Source PDF:** [Open original on district portal]({source_pdf_url})")
        out.append("")
    out.append('**Format:** Machine-extracted text from the source PDF')
    out.append("")
    out.append("</div>")
    out.append("")
    out.append(
        "!!! warning \"Machine-extracted text\""
    )
    out.append("")
    out.append(
        "    The text below was extracted automatically from the source "
        "PDF. Formatting (tables, columns, page breaks) is lost; some "
        "characters may be garbled where the PDF used non-standard "
        "encoding or rasterized text. **The source PDF is the "
        "authoritative copy** — link above. This extract exists so the "
        "content is searchable on this site and ingestible by AI tools."
    )
    out.append("")
    out.append("---")
    out.append("")
    # Wrap the raw text in a code block to preserve formatting and avoid
    # accidental markdown interpretation of the extracted content.
    out.append("```text")
    out.append(text.rstrip())
    out.append("```")
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--attachments", type=Path, required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True,
                    help="Output dir corpus/text/<year>/ — raw PDF text "
                         "extracts are NOT published on the website (PDFs "
                         "extract messily; humans should follow the PDF "
                         "link). They live in /corpus/ so AI tools / "
                         "NotebookLM can ingest the searchable text.")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    aid_lookup = load_aid_lookup(args.attachments)

    meetings = find_meetings_with_extracts(args.source_root)
    print(f"Scanning {len(meetings)} meeting folders for .txt extracts...")

    written = 0
    matched_aid = 0
    per_meeting_counts: dict[int, int] = {}
    per_meeting_entries: dict[int, list[dict]] = {}

    for meeting_dir in meetings:
        meeting_json = json.loads((meeting_dir / "meeting.json").read_text(encoding="utf-8"))
        mid = meeting_json.get("ID")
        if not isinstance(mid, int):
            continue
        title = meeting_json.get("Title", "Meeting")
        date_str = parse_date(meeting_json.get("TitleDateTime", ""))
        if not date_str:
            continue
        slug = slugify(title)
        meeting_page = f"../../{date_str}-{slug}.md"

        attachments_dir = meeting_dir / "attachments"
        meeting_record = aid_lookup.get(mid, {"attachments": []})

        mid_out = args.out / str(mid)
        any_written = False

        for txt_path in sorted(attachments_dir.glob("*.txt")):
            stem = txt_path.stem
            if not stem:
                continue
            # Skip if file is tiny / empty (likely failed extraction)
            try:
                text = txt_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if len(text.strip()) < 50:
                continue

            aid_match = find_aid_for_file(meeting_record, stem)
            if aid_match:
                matched_aid += 1
                source_pdf_url = aid_match["url"]
                attachment_title = aid_match["title"]
                section = aid_match["section"]
            else:
                source_pdf_url = None
                # Fall back to the file stem stripped of prefix
                attachment_title = re.sub(r"^[A-Z]_\d+_\d+_", "", stem)
                section = None

            md = render_extract(
                text=text,
                source_pdf_url=source_pdf_url,
                attachment_title=attachment_title,
                meeting_title=title,
                meeting_date=date_str,
                meeting_page=meeting_page,
                mid=mid,
                section=section,
            )
            if not any_written:
                mid_out.mkdir(parents=True, exist_ok=True)
                any_written = True
            out_name = safe_filename(stem) + ".md"
            (mid_out / out_name).write_text(md, encoding="utf-8")
            written += 1
            per_meeting_counts[mid] = per_meeting_counts.get(mid, 0) + 1
            per_meeting_entries.setdefault(mid, []).append({
                "filename": out_name,
                "title": attachment_title,
                "section": section or "",
                "has_source": bool(source_pdf_url),
                "source_url": source_pdf_url or "",
            })

        # Per-meeting index page so /text/<mid>/ resolves cleanly.
        if any_written:
            entries = sorted(per_meeting_entries[mid], key=lambda e: e["section"])
            idx = [
                f"# Document extracts — {title}",
                "",
                '<div class="meeting-meta" markdown>',
                "",
                f"**Meeting:** [{title}]({meeting_page}) — {date_str}",
                "",
                f"**Extracts:** {len(entries)} documents",
                "",
                "</div>",
                "",
                "Machine-extracted text of every PDF attachment from this "
                "meeting. Click any title to read the text; the **PDF** link "
                "on each extract page opens the original on the district "
                "portal.",
                "",
            ]
            for e in entries:
                label = f"{e['section']} — {e['title']}" if e["section"] else e["title"]
                idx.append(f"- [{label}]({e['filename']})")
            idx.append("")
            (mid_out / "index.md").write_text("\n".join(idx), encoding="utf-8")

    # Write an index for the text/ folder
    idx_lines = [
        f"# Document Text Extracts ({args.year})",
        "",
        f"Plain-text extractions of every PDF attachment from {args.year} "
        f"ICCSD board meetings — {written} documents across "
        f"{len(per_meeting_counts)} meetings. The originals stay on the "
        f"district portal; these extracts make the corpus searchable on "
        f"this site and ingestible by AI tools.",
        "",
        "Browse by meeting (newest first):",
        "",
    ]
    # Re-walk meetings sorted by date desc
    by_date: list[tuple[str, int, str]] = []
    for meeting_dir in meetings:
        meeting_json = json.loads((meeting_dir / "meeting.json").read_text(encoding="utf-8"))
        mid = meeting_json.get("ID")
        if not isinstance(mid, int) or mid not in per_meeting_counts:
            continue
        date_str = parse_date(meeting_json.get("TitleDateTime", ""))
        title = meeting_json.get("Title", "Meeting")
        by_date.append((date_str, mid, title))
    by_date.sort(key=lambda x: x[0], reverse=True)
    for date_str, mid, title in by_date:
        n = per_meeting_counts[mid]
        idx_lines.append(
            f"- **{date_str}** — {title} "
            f"([{n} document{'s' if n != 1 else ''}]({mid}/index.md))"
        )
    idx_lines.append("")
    (args.out / "index.md").write_text("\n".join(idx_lines), encoding="utf-8")

    print(f"Wrote {written} text-extract pages "
          f"({matched_aid} matched to AIDs, {written - matched_aid} unmatched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
