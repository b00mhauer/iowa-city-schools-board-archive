"""Collect AttachmentIDs for every ICCSD board meeting in a given year.

This is a slim, no-download version of the existing
`download_meeting.py` in the ICCSD client folder. It walks each meeting's
agenda tree via the eBoard Simbli API and records every
`(meeting_id, section_label, item_title, attachment_id, filename)` tuple to
a single JSON file.

The output JSON powers the meeting-page generator (build_pages.py): each
attachment becomes a direct deep-link of the form
    https://simbli.eboardsolutions.com/Meetings/Attachment.aspx?S=<sid>&AID=<aid>&MID=<mid>

Usage (from the repo root):

    python scripts/extract_aids.py \
        --meetings "C:/Users/MichaelParrott/480th Company/480th Back Offices - Documents/Clients - Contracts/ICCSD/all_meetings.json" \
        --year 2026 \
        --out data/attachments_2026.json

The script:
  - reuses a single Playwright Chrome context across all meetings (one
    Imperva challenge instead of 50),
  - writes JSON incrementally after every meeting (resumable),
  - skips MIDs already in the output file.

Resume / re-run is safe: delete the entry for a MID from the JSON to force
a re-scrape of that meeting.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

from playwright.sync_api import BrowserContext, Page, sync_playwright
from playwright_stealth import Stealth


BASE = "https://simbli.eboardsolutions.com"
SID = "36031992"  # ICCSD district ID — constant
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


# --- text helpers (copied from download_meeting.py for self-containment) ---

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t]+")


def html_to_text(s: str | None) -> str:
    if not s:
        return ""
    s = re.sub(r"</?(p|div|br|li|tr)[^>]*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<li[^>]*>", "- ", s, flags=re.IGNORECASE)
    s = _TAG.sub("", s)
    s = html.unescape(s)
    s = _WS.sub(" ", s)
    s = re.sub(r"\n[ \t]*", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# --- Simbli API helpers (cribbed from download_meeting.py) ---
#
# Page-side fetch is required: the eBoard site inspects Sec-Fetch-* /
# Origin metadata that Playwright's request context strips, and 403s
# anything without it.

_JS_FETCH_JSON = """
async ({url}) => {
    const r = await fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
    });
    return {status: r.status, body: await r.text(), ct: r.headers.get('content-type')||''};
}
"""


def build_url(path: str, params: dict[str, Any]) -> str:
    # The browser leaves '=' and '+' un-encoded in token values; Imperva
    # checks the raw form, so we must match.
    parts = []
    for k, v in params.items():
        sv = "" if v is None else str(v)
        parts.append(f"{k}={quote(sv, safe='=+/')}")
    return f"{BASE}{path}?{'&'.join(parts)}"


def api_json(page: Page, path: str, params: dict[str, Any]) -> dict:
    url = build_url(path, params)
    result = page.evaluate(_JS_FETCH_JSON, {"url": url})
    if result["status"] != 200:
        raise RuntimeError(
            f"{path} returned {result['status']} ({result.get('ct')}) "
            f"body={result.get('body','')[:200]!r}"
        )
    return json.loads(result["body"])


def extract_ids(page_html: str) -> dict[str, str]:
    def grab(pattern: str) -> str:
        m = re.search(pattern, page_html)
        if not m:
            raise RuntimeError(f"Could not find pattern: {pattern}")
        return m.group(1)

    return {
        "endid": grab(r"var enSID\s*=\s*'([^']+)'"),
        "enmid": grab(r"var enMeetingID\s*=\s*'([^']+)'"),
        "sct": grab(r'"SecurityToken"\s*:\s*"([^"]+)"'),
    }


def flatten_items(tree: dict) -> list[dict]:
    out: list[dict] = []

    def walk(node: dict, parent_chain: list[str] | None = None) -> None:
        chain = list(parent_chain or [])
        bullet = node.get("bulletLabel", "")
        if bullet:
            chain = chain + [bullet]
        out.append(
            {
                "encrypted_id": node["ID"],
                "agenda_id": node.get("AgendaID"),
                "title": node.get("Title") or "",
                "level": node.get("Level"),
                "chain": chain,
                "has_attachment": bool(node.get("HasAttachment")),
                "deleted": bool(node.get("Deleted")),
            }
        )
        for child in node.get("Children") or []:
            walk(child, chain)

    for it in tree.get("Items") or []:
        walk(it)
    return [x for x in out if not x["deleted"]]


def chain_label(chain: list[str]) -> str:
    return ".".join(c if not c.isdigit() else f"{int(c):02d}" for c in chain) or "X"


# --- per-meeting scrape ---


def navigate_to_meeting(page: Page, mid: str) -> dict[str, str]:
    """Load the meeting view page and wait through the Imperva challenge.

    Returns the embedded enSID/enMeetingID/SecurityToken values.
    """
    meeting_url = f"{BASE}/SB_Meetings/ViewMeeting.aspx?S={SID}&MID={mid}"
    page.goto(meeting_url, wait_until="domcontentloaded", timeout=60_000)
    deadline_ms = 60_000
    waited = 0
    content = ""
    while waited < deadline_ms:
        content = page.content()
        if "var enSID" in content:
            break
        page.wait_for_timeout(1_000)
        waited += 1_000
    else:
        raise RuntimeError(
            f"MID {mid}: meeting page never loaded (Imperva still up after 60s)"
        )
    return extract_ids(content)


def scrape_meeting(page: Page, mid: str, title: str, title_dt: str) -> dict:
    ids = navigate_to_meeting(page, mid)

    # GetMeeting just for canonical title/date (the all_meetings.json values
    # are sometimes stale or missing the AMENDED suffix).
    meeting_meta = api_json(
        page,
        "/Services/api/GetMeeting/",
        {
            "endid": ids["endid"],
            "enmid": ids["enmid"],
            "entz": "4DPD0XoPkbiKsuou4JEdqg==",
            "searchText": "",
            "matchType": "",
        },
    )

    tree = api_json(
        page,
        "/Services/api/MeetingView/GetItemsTreeDTO/",
        {
            "sct": ids["sct"],
            "endid": ids["endid"],
            "enmid": ids["enmid"],
            "enuid": "",
            "v": "",
        },
    )
    items = flatten_items(tree)

    attachments: list[dict] = []
    seen_aids: set[int] = set()
    items_with_atts = [i for i in items if i["has_attachment"]]

    for item in items_with_atts:
        try:
            detail = api_json(
                page,
                "/Services/api/MeetingView/GetMeetingItemDetailsModel/",
                {
                    "sct": ids["sct"],
                    "endid": ids["endid"],
                    "enmid": ids["enmid"],
                    "enitemid": item["encrypted_id"],
                    "enuid": "",
                    "view": "",
                    "stab": "1",
                },
            )
        except Exception as e:
            print(f"    item {chain_label(item['chain'])}: detail fetch failed: {e}",
                  file=sys.stderr)
            continue

        for ic in detail.get("ItemContents") or []:
            for att in ic.get("Attachments") or []:
                aid = att.get("AttachmentID")
                if aid is None or aid in seen_aids:
                    continue
                seen_aids.add(aid)
                filename = att.get("FileName") or f"attachment_{aid}"
                attachments.append({
                    "aid": aid,
                    "filename": filename,
                    "title": att.get("Title") or filename,
                    "ext": att.get("FileExtension") or "",
                    "section": chain_label(item["chain"]),
                    "item_title": item["title"],
                    "url": f"{BASE}/Meetings/Attachment.aspx?S={SID}&AID={aid}&MID={mid}",
                })

    return {
        "mid": int(mid),
        "title": meeting_meta.get("Title") or title,
        "title_datetime": meeting_meta.get("TitleDateTime") or title_dt,
        "source_url": f"{BASE}/SB_Meetings/ViewMeeting.aspx?S={SID}&MID={mid}",
        "item_count": len(items),
        "items_with_attachments": len(items_with_atts),
        "attachments": attachments,
    }


# --- driver ---


def load_meetings(meetings_path: Path, year: int) -> list[dict]:
    with open(meetings_path, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for m in data:
        if not m.get("IsPublic"):
            continue
        dt = m.get("DateTime", "")
        if not dt.startswith(f"{year}-"):
            continue
        out.append(m)
    out.sort(key=lambda m: m["DateTime"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--meetings", type=Path, required=True,
                    help="Path to all_meetings.json")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True,
                    help="Output JSON path (resumed across runs)")
    ap.add_argument("--headed", action="store_true", help="Show the browser window")
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap the number of meetings (for testing)")
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    # Load existing output for resume.
    existing: dict[str, dict] = {}
    if args.out.exists():
        try:
            existing = json.loads(args.out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"WARN: {args.out} is not valid JSON, starting fresh", file=sys.stderr)
            existing = {}

    meetings = load_meetings(args.meetings, args.year)
    if args.limit is not None:
        meetings = meetings[:args.limit]

    todo = [m for m in meetings if str(m["MID"]) not in existing]
    print(f"{len(meetings)} {args.year} public meetings total, "
          f"{len(existing)} already done, {len(todo)} to scrape", flush=True)

    if not todo:
        print("Nothing to do.")
        return 0

    started = time.monotonic()
    with Stealth().use_sync(sync_playwright()) as pw:
        browser = pw.chromium.launch(
            channel="chrome",
            headless=not args.headed,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context: BrowserContext = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/Chicago",
        )
        page = context.new_page()

        for idx, m in enumerate(todo, 1):
            mid = str(m["MID"])
            label = f"[{idx}/{len(todo)}] MID {mid} ({m['DateTime'][:10]}, {m['Type']})"
            print(f"{label} {m['Title'][:80]}", flush=True)
            try:
                rec = scrape_meeting(page, mid, m["Title"], m["DateTime"])
                existing[mid] = rec
                # Persist after every meeting — partial progress is durable.
                args.out.write_text(json.dumps(existing, indent=2), encoding="utf-8")
                print(f"  -> {len(rec['attachments'])} attachments", flush=True)
            except Exception as e:
                print(f"  !! failed: {e}", file=sys.stderr, flush=True)

        context.close()
        browser.close()

    elapsed = time.monotonic() - started
    print(f"\nDone. {len(existing)} meetings in {args.out}. "
          f"Elapsed: {elapsed:.0f}s.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
