"""Refresh EVERYTHING — the master orchestrator.

Runs the full pipeline in the right order, then commits and pushes.
This is what to run when someone says "refresh everything."

Pipeline:

   1.  list_meetings.py            (ICCSD folder) — refresh master meeting list
   2.  bulk_download.py            (ICCSD folder) — download agendas for any new MIDs
   3.  extract_aids.py             — scrape attachment IDs for new MIDs (resumable)
   4.  build_pages.py              — regenerate meeting pages
   4b. extract_pdf_text.py         (ICCSD folder) — extract text from attachment PDFs
                                     (writes a .txt sibling next to each .pdf,
                                      resumable; needs pdfplumber)
   4c. publish_extracts.py         — publish extracted .txt files into
                                     corpus/text/<year>/<mid>/*.md so AI tools
                                     can ingest the searchable text
   4d. publish_audited_financials.py — refresh docs/audited-financials/
   5.  refresh_press.py            (no --auto-commit) — mirror news + chain
                                     timeline + topic pages + home Latest +
                                     LLM manifest + LLM footers
   6.  mkdocs build --strict       — verify
   7.  git add -A + commit + push  — one commit covering everything

Idempotent at every step. Re-running with no source changes ends in a
clean no-op commit (or skips the commit entirely).

Usage (no args needed — paths are configured below):

    python scripts/refresh_all.py [--no-push] [--skip-list] [--skip-download]
                                  [--skip-audited] [--skip-corpus]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# --- paths ---

REPO_ROOT = Path(__file__).parent.parent.resolve()
SCRIPTS = REPO_ROOT / "scripts"

ICCSD_ROOT = Path(
    r"C:\Users\MichaelParrott\480th Company\480th Back Offices - Documents"
    r"\Clients - Contracts\ICCSD"
)
ICCSD_YEAR = ICCSD_ROOT / "2026"
ALL_MEETINGS = ICCSD_ROOT / "all_meetings.json"
NEWS_SOURCE = ICCSD_YEAR / "News_2026.md"
AUDITED_SOURCE = ICCSD_ROOT / "Financial analysis" / "Audited Financials"

YEAR = 2026


# --- helpers ---


def run(cmd: list[str], cwd: Path | None = None, check: bool = True,
        capture: bool = False, label: str = "") -> subprocess.CompletedProcess:
    if label:
        print(f"\n=== {label} ===")
    if not capture:
        return subprocess.run(cmd, cwd=cwd, check=check)
    return subprocess.run(cmd, cwd=cwd, check=check,
                          capture_output=True, text=True)


def py(name: str, args: list[str], cwd: Path | None = None,
       label: str = "") -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPTS / name), *args]
    return run(cmd, cwd=cwd, label=label)


def py_external(path: Path, args: list[str], cwd: Path | None = None,
                label: str = "") -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(path), *args]
    return run(cmd, cwd=cwd, label=label)


# --- main ---


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--no-push", action="store_true",
                    help="Run the chain and commit, but don't push.")
    ap.add_argument("--skip-list", action="store_true",
                    help="Skip refreshing the master meeting list (use if "
                         "Simbli is rate-limiting or you just ran it).")
    ap.add_argument("--skip-download", action="store_true",
                    help="Skip downloading agendas for new MIDs. Useful when "
                         "Playwright/Chrome isn't available — the rest of the "
                         "chain still runs.")
    ap.add_argument("--skip-audited", action="store_true",
                    help="Skip republishing audited financials.")
    ap.add_argument("--skip-corpus", action="store_true",
                    help="Skip PDF text extraction and corpus publishing "
                         "(Step 4b + 4c). Useful when pdfplumber isn't "
                         "installed or you only need meeting pages refreshed.")
    args = ap.parse_args()

    started = datetime.now(timezone.utc)
    print(f"refresh_all started at {started.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  REPO_ROOT: {REPO_ROOT}")
    print(f"  ICCSD ROOT: {ICCSD_ROOT}")

    # --- Step 1: refresh master meeting list ---
    if args.skip_list:
        print("\nSkipping list_meetings.py (per --skip-list).")
    else:
        list_meetings = ICCSD_ROOT / "list_meetings.py"
        if list_meetings.exists():
            py_external(list_meetings, ["--json", str(ALL_MEETINGS)],
                        cwd=ICCSD_ROOT,
                        label="Step 1/7: refresh master meeting list")
        else:
            print(f"WARN: {list_meetings} not found; skipping list refresh.")

    # --- Step 2: download agendas for new MIDs ---
    if args.skip_download:
        print("\nSkipping bulk_download.py (per --skip-download).")
    else:
        bulk_download = ICCSD_ROOT / "bulk_download.py"
        if bulk_download.exists():
            try:
                py_external(bulk_download, ["--year", str(YEAR)],
                            cwd=ICCSD_ROOT,
                            label="Step 2/7: download new meeting agendas")
            except subprocess.CalledProcessError as e:
                print(f"WARN: bulk_download exit {e.returncode} — "
                      f"continuing (some meetings may not be downloaded).")
        else:
            print(f"WARN: {bulk_download} not found; skipping downloads.")

    # --- Step 3: scrape AIDs for new MIDs ---
    py("extract_aids.py", [
        "--meetings", str(ALL_MEETINGS),
        "--year", str(YEAR),
        "--out", str(REPO_ROOT / "data" / f"attachments_{YEAR}.json"),
    ], label="Step 3/7: scrape attachment IDs for new meetings")

    # --- Step 4: build meeting pages ---
    py("build_pages.py", [
        "--source-root", str(ICCSD_YEAR),
        "--attachments", str(REPO_ROOT / "data" / f"attachments_{YEAR}.json"),
        "--meetings-json", str(ALL_MEETINGS),
        "--year", str(YEAR),
        "--out", str(REPO_ROOT / "docs" / "meetings" / str(YEAR)),
        "--summaries", str(REPO_ROOT / "data" / f"summaries_{YEAR}.json"),
        "--corpus-root", str(REPO_ROOT / "corpus"),
    ], label="Step 4/7: build meeting pages")

    # --- Step 4b: extract text from attachment PDFs ---
    # Walks the ICCSD year folder, writes a .txt sibling next to each .pdf
    # using pdfplumber. Resumable — skips files already extracted. Some
    # scanned/image-only PDFs come back empty; those are silently skipped
    # downstream by publish_extracts.
    if args.skip_corpus:
        print("\nSkipping PDF text extraction (per --skip-corpus).")
    else:
        extract_pdf_text = ICCSD_ROOT / "extract_pdf_text.py"
        if extract_pdf_text.exists() and ICCSD_YEAR.is_dir():
            try:
                py_external(extract_pdf_text,
                            [str(ICCSD_YEAR), "--workers", "6"],
                            cwd=ICCSD_ROOT,
                            label="Step 4b/7: extract text from PDF "
                                  "attachments (pdfplumber)")
            except subprocess.CalledProcessError as e:
                print(f"WARN: extract_pdf_text exit {e.returncode} — "
                      f"continuing (corpus text may be incomplete).")
        else:
            print(f"WARN: {extract_pdf_text} not found or year dir missing; "
                  f"skipping PDF text extraction.")

    # --- Step 4c: publish extracted text into corpus/text/<year>/<mid>/ ---
    # Reads .txt files written by Step 4b and the AID lookup from Step 3,
    # then writes one markdown page per attachment under
    # corpus/text/<year>/<mid>/<slug>.md. IMPORTANT: --out must include the
    # year segment, or you'll get duplicate dirs at the wrong path level.
    if args.skip_corpus:
        print("\nSkipping corpus publish (per --skip-corpus).")
    else:
        try:
            py("publish_extracts.py", [
                "--source-root", str(ICCSD_YEAR),
                "--attachments", str(REPO_ROOT / "data"
                                     / f"attachments_{YEAR}.json"),
                "--year", str(YEAR),
                "--out", str(REPO_ROOT / "corpus" / "text" / str(YEAR)),
            ], label="Step 4c/7: publish extracted text into corpus")
        except subprocess.CalledProcessError as e:
            print(f"WARN: publish_extracts exit {e.returncode} — "
                  f"continuing (corpus may not reflect latest extracts).")

    # --- Step 4d: publish audited financials (idempotent) ---
    if not args.skip_audited and AUDITED_SOURCE.is_dir():
        py("publish_audited_financials.py", [
            "--source", str(AUDITED_SOURCE),
            "--out", str(REPO_ROOT / "docs" / "audited-financials"),
        ], label="Step 4d/7: publish audited financials")

    # --- Step 5: mirror press + downstream chain (NO --auto-commit:
    #             we do one combined commit at the bottom) ---
    py("refresh_press.py", [
        "--source", str(NEWS_SOURCE),
        "--year", str(YEAR),
        "--out", str(REPO_ROOT / "docs" / "press" / f"{YEAR}.md"),
    ], label="Step 5/7: refresh press + regen timeline/topics/home/manifest/footers")

    # --- Step 6: strict build ---
    run(["mkdocs", "build", "--strict"],
        cwd=REPO_ROOT,
        label="Step 6/7: mkdocs build --strict")

    # --- Step 7: commit + push (only if something changed) ---
    print("\n=== Step 7/7: git commit + push ===")
    status = run(["git", "status", "--porcelain"],
                 cwd=REPO_ROOT, capture=True).stdout
    if not status.strip():
        print("git: working tree clean — nothing to commit. Done.")
        return 0
    n_changed = sum(1 for line in status.splitlines() if line.strip())
    print(f"git: {n_changed} change(s) staged.")
    run(["git", "add", "-A"], cwd=REPO_ROOT)
    ts = started.strftime("%Y-%m-%d")
    run(["git", "commit", "-m", f"refresh_all ({ts}): full pipeline"],
        cwd=REPO_ROOT)
    if args.no_push:
        print("git: committed (push skipped per --no-push).")
    else:
        run(["git", "push"], cwd=REPO_ROOT)
        print("git: pushed.")

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    print(f"\nrefresh_all complete in {elapsed:.0f}s.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
