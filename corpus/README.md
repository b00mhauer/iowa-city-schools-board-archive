# Corpus

Raw source material — meeting transcripts and PDF text extracts — that
**is not published as web pages** on the
[Iowa City Schools Board Archive site](https://b00mhauer.github.io/iowa-city-schools-board-archive/),
but **is** in this git repository for ingestion by AI tools (NotebookLM,
RAG pipelines, etc.).

## Layout

```
corpus/
├── transcripts/
│   └── 2026/
│       └── <YYYY-MM-DD>-<slug>.md   # YouTube auto-captions, paragraph-
│                                    # broken with timestamps as anchors
└── text/
    └── 2026/
        └── <MID>/
            ├── index.md             # list of every extract for this meeting
            └── <PREFIX>_<stem>.md   # one per PDF attachment, raw text
```

## Why these aren't on the website

- **Transcripts** are YouTube auto-generated captions. They have no
  speaker labels, frequent transcription errors, and read as a wall of
  text. They're useful as a search/AI index but inappropriate as
  human-facing pages.
- **PDF text extracts** preserve layout artifacts from the source PDFs
  (vertical text rendered as reversed strings, header/footer noise,
  table structure lost). They're useful for full-text search and AI
  ingestion but unreadable as primary content.

## What humans use instead

The [meeting pages on the site](https://b00mhauer.github.io/iowa-city-schools-board-archive/meetings/2026/)
carry synthesized "What happened" summaries of each substantive meeting,
direct YouTube links (with timestamp anchors at notable moments where
known), and deep-links to each supporting PDF on the district portal.

## Regeneration

These files are rebuilt from the source ICCSD client folder by:

```
python scripts/build_transcripts.py --source-root <path> --year 2026 --out corpus/transcripts/2026
python scripts/publish_extracts.py --source-root <path> --attachments data/attachments_2026.json --year 2026 --out corpus/text/2026
```
