"""Daily refresh entry point for the press page.

Designed to be called by a Claude Co-work scheduled task (or a local cron)
after the source News_<YEAR>.md has been updated. This script handles
the mechanical side of the refresh:

  1. Read the source News_<YEAR>.md (SharePoint/OneDrive synced locally)
  2. Mirror it into docs/press/<year>.md with the right frontmatter
  3. Diff vs. the previously published version — by H3 article titles
  4. Append a dated entry to data/press_changelog.md listing what was
     added or removed
  5. (Optional, with --auto-commit) git add/commit/push

What this script intentionally does NOT do:

  - Rewrite Timeline / Topics / Administrators pages based on the new
    articles. That's editorial judgment work; doing it automatically
    risks silently inserting wrong claims. The changelog exists so the
    archive maintainer (or Claude in a separate, supervised session)
    can review accumulated additions periodically and update the
    synthesis pages by hand.

Usage:

    python scripts/refresh_press.py \\
        --source "C:/Users/.../ICCSD/2026/News_2026.md" \\
        --year 2026 \\
        --out docs/press/2026.md \\
        --auto-commit

Add --no-push to commit but not push. Add --dry-run to preview without
writing anything.
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path


_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_H3_RE = re.compile(r"^### (.+)$", re.MULTILINE)


def _strip_frontmatter(s: str) -> str:
    return _FRONTMATTER_RE.sub("", s)


def _article_titles(text: str) -> list[str]:
    """Return H3 article titles in document order. Used for diffing."""
    return [m.group(1).strip() for m in _H3_RE.finditer(text)]


def _frontmatter(year: int) -> str:
    return f"---\ntitle: {year} News Coverage\n---\n\n"


def _ensure_changelog(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Press Refresh Changelog\n"
        "\n"
        "Auto-generated log of what changed each time the press page was\n"
        "refreshed from the source `News_<YEAR>.md`. Articles are identified\n"
        "by their H3 heading text.\n"
        "\n"
        "Use this log to drive periodic **editorial review** of the\n"
        "Timeline, Topics, and Administrators pages — those don't update\n"
        "automatically (and shouldn't, because synthesis is human judgment).\n"
        "\n",
        encoding="utf-8",
    )


def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--source", type=Path, required=True,
                    help="Path to source News_<YEAR>.md (locally-synced SharePoint).")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True,
                    help="Output path docs/press/<year>.md")
    ap.add_argument("--changelog", type=Path,
                    default=Path("data") / "press_changelog.md",
                    help="Changelog markdown to append to.")
    ap.add_argument("--auto-commit", action="store_true",
                    help="git add/commit/push when there are real changes.")
    ap.add_argument("--no-push", action="store_true",
                    help="With --auto-commit, commit but don't push.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would happen without writing or committing.")
    args = ap.parse_args()

    if not args.source.exists():
        print(f"ERROR: source not found: {args.source}", file=sys.stderr)
        return 2

    # --- Step 1: read source ---
    new_text = args.source.read_text(encoding="utf-8")
    new_body = _strip_frontmatter(new_text)
    new_titles = _article_titles(new_body)
    new_set = set(new_titles)

    # --- Step 2: load current published version (if any) ---
    old_titles: list[str] = []
    if args.out.exists():
        old_text = args.out.read_text(encoding="utf-8")
        old_titles = _article_titles(_strip_frontmatter(old_text))
    old_set = set(old_titles)

    added = [t for t in new_titles if t not in old_set]
    removed = [t for t in old_titles if t not in new_set]

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    print(f"Source : {args.source}")
    print(f"Target : {args.out}")
    print(f"Articles in source: {len(new_titles)}  (was {len(old_titles)})")
    print(f"Added  : {len(added)}")
    print(f"Removed: {len(removed)}")
    if added:
        print("  New article headings:")
        for t in added:
            print(f"    + {t[:100]}")
    if removed:
        print("  Removed article headings:")
        for t in removed:
            print(f"    - {t[:100]}")

    if args.dry_run:
        print("DRY RUN: no files written.")
        return 0

    # --- Step 3: mirror with frontmatter ---
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(_frontmatter(args.year) + new_body, encoding="utf-8", newline="\n")
    print(f"Wrote {args.out} ({args.out.stat().st_size:,} bytes).")

    # --- Step 4: append changelog entry if there were article-level changes ---
    if added or removed:
        _ensure_changelog(args.changelog)
        entry_lines = [f"\n## {timestamp}\n", "\n"]
        if added:
            entry_lines.append("### Added\n\n")
            for t in added:
                entry_lines.append(f"- {t}\n")
            entry_lines.append("\n")
        if removed:
            entry_lines.append("### Removed\n\n")
            for t in removed:
                entry_lines.append(f"- {t}\n")
            entry_lines.append("\n")
        with open(args.changelog, "a", encoding="utf-8", newline="\n") as f:
            f.writelines(entry_lines)
        print(f"Appended {len(added) + len(removed)} change(s) to {args.changelog}.")

    # --- Step 4b: chain downstream generators that depend on press content ---
    # These are deterministic regenerators — they update the Timeline and the
    # per-topic press sections so the site reflects the new press file the
    # same day. Both are pure-Python aggregators (no LLM, no synthesis); a
    # changelog of what they produced is on stdout for debugging.
    scripts_dir = Path(__file__).parent
    repo_root = scripts_dir.parent

    iccsd_meetings_json = (
        Path("C:/Users/MichaelParrott/480th Company/480th Back Offices - Documents")
        / "Clients - Contracts" / "ICCSD" / "all_meetings.json"
    )

    if iccsd_meetings_json.exists():
        try:
            _run([
                sys.executable, str(scripts_dir / "build_timeline.py"),
                "--press", str(args.out),
                "--summaries", str(repo_root / "data" / f"summaries_{args.year}.json"),
                "--anchors", str(repo_root / "data" / f"anchor_events_{args.year}.json"),
                "--meetings-json", str(iccsd_meetings_json),
                "--year", str(args.year),
                "--out", str(repo_root / "docs" / "timeline.md"),
            ])
            print(f"refreshed: docs/timeline.md")
        except subprocess.CalledProcessError as e:
            print(f"WARN: build_timeline failed: {e.stderr}", file=sys.stderr)
        try:
            _run([
                sys.executable, str(scripts_dir / "build_topics.py"),
                "--attachments", str(repo_root / "data" / f"attachments_{args.year}.json"),
                "--press", str(args.out),
                "--out", str(repo_root / "docs" / "topics"),
            ])
            print(f"refreshed: docs/topics/*.md")
        except subprocess.CalledProcessError as e:
            print(f"WARN: build_topics failed: {e.stderr}", file=sys.stderr)
        try:
            _run([
                sys.executable, str(scripts_dir / "build_home.py"),
                "--index", str(repo_root / "docs" / "index.md"),
                "--summaries", str(repo_root / "data" / f"summaries_{args.year}.json"),
                "--press", str(args.out),
                "--meetings-json", str(iccsd_meetings_json),
                "--year", str(args.year),
            ])
            print(f"refreshed: docs/index.md (Latest block)")
        except subprocess.CalledProcessError as e:
            print(f"WARN: build_home failed: {e.stderr}", file=sys.stderr)
        try:
            _run([
                sys.executable, str(scripts_dir / "build_llms_manifest.py"),
                "--summaries", str(repo_root / "data" / f"summaries_{args.year}.json"),
                "--press", str(args.out),
                "--anchors", str(repo_root / "data" / f"anchor_events_{args.year}.json"),
                "--attachments", str(repo_root / "data" / f"attachments_{args.year}.json"),
                "--meetings-json", str(iccsd_meetings_json),
                "--year", str(args.year),
                "--out", str(repo_root / "docs" / "llms.md"),
            ])
            print(f"refreshed: docs/llms.md (LLM manifest)")
        except subprocess.CalledProcessError as e:
            print(f"WARN: build_llms_manifest failed: {e.stderr}", file=sys.stderr)
    else:
        print(
            f"NOTE: {iccsd_meetings_json} not found — skipping downstream "
            f"generators. Run them manually with the right paths when on "
            f"the maintainer's machine."
        )

    # --- Step 5: optional commit / push ---
    if args.auto_commit:
        # Check working tree for any actual filesystem changes (cover the
        # case where mirror was a no-op due to byte-identical source).
        # Include downstream-generated files too.
        downstream = [
            str(repo_root / "docs" / "timeline.md"),
            str(repo_root / "docs" / "topics" / "budget.md"),
            str(repo_root / "docs" / "topics" / "superintendent.md"),
            str(repo_root / "docs" / "topics" / "facilities.md"),
            str(repo_root / "docs" / "topics" / "policies.md"),
            str(repo_root / "docs" / "topics" / "boundaries.md"),
            str(repo_root / "docs" / "topics" / "index.md"),
            str(repo_root / "docs" / "index.md"),
            str(repo_root / "docs" / "llms.md"),
        ]
        status = _run([
            "git", "status", "--porcelain",
            str(args.out), str(args.changelog), *downstream,
        ], check=False).stdout
        if not status.strip():
            print("git: no filesystem changes after mirror; skipping commit.")
            return 0

        msg_parts = [f"press: daily refresh ({timestamp[:10]})"]
        if added:
            msg_parts.append(f"+{len(added)} article(s)")
        if removed:
            msg_parts.append(f"-{len(removed)} removed")
        msg = " — ".join(msg_parts) if len(msg_parts) > 1 else msg_parts[0]

        _run([
            "git", "add",
            str(args.out), str(args.changelog), *downstream,
        ])
        _run(["git", "commit", "-m", msg])
        print(f"git: committed — {msg}")

        if not args.no_push:
            try:
                _run(["git", "push"])
                print("git: pushed.")
            except subprocess.CalledProcessError as e:
                print(f"git push failed (non-fatal in scheduled context): {e.stderr}",
                      file=sys.stderr)
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
