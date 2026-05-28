# Press refresh workflow

Two-tier model — separates the mechanical part (safe to automate daily)
from the editorial part (judgment-required, on-demand).

## Tier 1 — Daily mirror (automated)

Run `scripts/refresh_press.py` from Claude Co-work (or any other
scheduled context that has Python + git access + a clone of this repo).
Recommended command:

```
python scripts/refresh_press.py ^
    --source "C:/Users/MichaelParrott/480th Company/480th Back Offices - Documents/Clients - Contracts/ICCSD/2026/News_2026.md" ^
    --year 2026 ^
    --out docs/press/2026.md ^
    --auto-commit
```

What it does:

1. Mirrors the SharePoint-synced `News_2026.md` into `docs/press/2026.md`
   (with the right MkDocs frontmatter).
2. Diffs the new article list against the previous published version
   by H3 headings.
3. Appends a dated entry to `data/press_changelog.md` listing **added**
   and **removed** article headings.
4. With `--auto-commit`: stages those two files, commits with a message
   like `press: daily refresh (2026-05-29) — +3 article(s)`, and pushes.

What it does NOT do:

- Rewrite Timeline / Topics / Administrators pages with new news-derived
  facts. That's the Tier 2 work — see below.

Edge cases handled:

- Source file unchanged since last run → script is a no-op (no commit,
  exit 0).
- Source file present but with no article-level changes (e.g. only a typo
  fixed) → script still mirrors but doesn't append a changelog entry and
  may not commit if the byte-identical output didn't change anything.
- `--dry-run` shows what would happen without writing or committing.
- `--no-push` commits but doesn't push (useful for testing).

## Tier 2 — Editorial refresh (on demand)

When `data/press_changelog.md` shows a meaningful set of new articles
that aren't yet reflected in the synthesis pages, Michael (or a
supervised Claude session) does an editorial pass:

1. Read recent entries in `data/press_changelog.md`.
2. For each new article: read the full entry in `docs/press/2026.md`.
3. Decide what (if anything) the article adds to the synthesis pages:
   - `docs/timeline.md` — date-anchored events
   - `docs/topics/budget.md`, `superintendent.md`, `facilities.md`,
     `policies.md`, `boundaries.md` — thematic narratives
   - `docs/people/administrators.md` — leadership transitions
   - `docs/people/board-members.md` — board-member statements / votes
4. Make the edits with citations back to `press/2026.md#<anchor>`.
5. Run `mkdocs build --strict` locally to confirm anchors resolve.
6. Commit with `press: editorial refresh — incorporate <N> press items`.

A reasonable cadence: weekly during active news cycles, monthly during
quieter periods. Don't let the changelog drift more than a few weeks
unreviewed — old un-incorporated items become invisible to readers of
the synthesis pages.

## Why this two-tier model

- **Daily mechanical refresh** keeps the press index always current
  (visitors who arrive looking for "the article KCRG published yesterday"
  find it).
- **On-demand editorial review** keeps the synthesis pages accurate
  without risking auto-generated wrong claims. Synthesis is a curatorial
  activity; the right cadence is "when the maintainer can review,"
  not "every 24 hours regardless."
- The changelog is the **interface** between the two tiers — it tells
  the editorial step exactly what's been added since last review.

## If you want me (Claude) to do the editorial refresh

Open a session in this repo and say something like:

> Read `data/press_changelog.md` entries since the last editorial
> refresh, identify any items not yet reflected in `docs/timeline.md`
> or `docs/topics/*.md` or `docs/people/administrators.md`, and
> incorporate them with citations back to the press page anchors.
> Run `mkdocs build --strict` and push when done.

I'll do the synthesis work, leaving the source pages cleanly updated.
