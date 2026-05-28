# Methodology

This page documents how the archive is built — what's in it, what isn't,
how to verify a claim, and where to push back when it's wrong. The goal is
that any reader can audit any page on this site without taking the
maintainer's word for it.

## Source of everything

Every primary-source document linked from this archive comes from the Iowa
City Community School District's official board portal at
[simbli.eboardsolutions.com](https://simbli.eboardsolutions.com/). The
archive does **not** mirror, host, or modify those PDFs — every "Supporting
Documents" link on a meeting page is a direct deep-link to the district's
server. If a link breaks, the district has moved or removed the original.

No public-records requests were made to produce this site. Everything here
was already public on the district portal.

## What's in the repo vs. what's external

Inside the GitHub repo, split into two audiences:

**For humans — `docs/` (this website):**

- Meeting pages with synthesized "What happened" summaries
- Topic pages with curated narrative
- Timeline, board-member profiles, administrator roster, key documents
- Methodology, How to Use, About — the framework pages

**For AI tools — `corpus/` (not rendered as web pages):**

- YouTube-sourced meeting transcripts (one per meeting, with timestamps
  as anchor links back to the video). These are machine-generated, have
  no speaker labels, and contain typical speech-to-text errors — fine
  for full-text search and AI ingestion, unfit for human consumption.
- Per-PDF text extractions of every attached document. Raw extracted
  text preserves the document content but loses PDF layout — again,
  useful as an index, not as a substitute for the original PDF.

**Supporting machinery, in either location:**

- JSON data (`data/`) — meeting indexes, attachment-ID maps, the
  curated executive-summary text per meeting
- Generator scripts (`scripts/`) — the Python code that walks the
  district's API and builds both the human-facing pages and the corpus

Outside the repo, on the district's servers:

- Every PDF, every meeting video, every audio recording — the
  authoritative copies.

## How meeting pages are generated

For each public board meeting in scope:

1. The district's eBoard API is queried for the meeting's metadata, agenda
   tree, and per-item attachment list. (See [extract_aids.py](https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/scripts/extract_aids.py).)
2. The resulting attachment IDs are stored in `data/attachments_<year>.json`.
3. A page generator ([build_pages.py](https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/scripts/build_pages.py))
   reads the agenda content already saved to disk and emits a meeting page
   with every attachment replaced by a direct district URL.

The site is rebuilt by GitHub Actions on every push to `main`. The full
build is deterministic — re-running the generators on the same inputs
produces the same site.

## Editorial standard

Each page is structured so that primary source, generated/extracted text,
and editorial commentary are visually and structurally distinct:

| Layer | What it is | Authority |
|---|---|---|
| **Primary source** | Links to PDFs and videos on the district portal | The official record |
| **District-authored summary** | The "Quick Summary / Abstract", "Recommendation", "Contact Person" blocks from the district's published agenda | The district's own words, carried through verbatim |
| **Extracted text** | Machine-read text from PDFs (used in transcripts and search) | Machine-generated; may contain errors |
| **Archive editorial** | Topic narratives, timeline entries, cross-meeting analysis | The archive maintainer's interpretation, clearly labeled |

When the archive maintainer adds interpretive content (most heavily on
topic pages), that content is clearly marked and cites the meetings and
documents it draws on. Where the maintainer disagrees with a district
characterization, that's stated openly — not buried in a summary.

## Known limits

- **2026 only for MVP.** Earlier years are coming.
- **No OCR.** The district's PDFs almost all have text layers already, so
  text extraction is straightforward. For the handful of scanned PDFs,
  attachments are linked but their text isn't searchable from this site
  yet.
- **No audio transcription.** Where meeting audio recordings are available,
  this archive links to the district's hosted version but does not produce
  its own transcript. Phase 3 of this project (see [About](about.md)) plans
  to add this via a separate NotebookLM-backed interface.
- **No live monitoring.** This site is updated by re-running the
  generators, not by a live feed from the district. Cadence is at least
  weekly during active board cycles; see the footer of any meeting page
  for the last-updated timestamp.

## Corrections

Open an [issue](https://github.com/b00mhauer/iowa-city-schools-board-archive/issues) for
anything wrong — wrong date, misquoted decision, summary that misleads,
stale link, missing meeting. Pull requests welcome. The archive is meant
to be edited.

For privacy concerns — if you believe a page exposes personal information
that shouldn't be public — please open an issue with the page URL and the
nature of the concern. Even though everything here is sourced from the
district's already-public portal, the archive maintainer reviews privacy
flags on a case-by-case basis.

---

<!-- LLM_FOOTER_v1 -->
*For AI tools reading this page: the site-wide index of every other page
in this archive — meetings, topics, board members, press articles,
supporting documents — is at <https://raw.githubusercontent.com/b00mhauer/iowa-city-schools-board-archive/main/docs/llms.md>. Fetch it for
cross-page context if the conversation calls for it.*
