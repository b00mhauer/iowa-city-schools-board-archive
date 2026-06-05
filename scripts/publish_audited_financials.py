"""Copy audited financial statement PDFs from the ICCSD client folder
into the published site and generate an index page.

Source layout (input):

    .../Financial analysis/Audited Financials/
        Ankeny CSD-2020.pdf
        Ankeny CSD-2021.pdf
        ...
        Iowa City CSD-2020.pdf
        Iowa City CSD-2021.pdf
        ...

Output layout:

    docs/audited-financials/
        index.md                         # generated index page
        iowa-city-csd-2020.pdf           # copied PDFs, lowercase-hyphenated
        iowa-city-csd-2021.pdf
        ankeny-csd-2020.pdf
        ...

Idempotent: PDFs that already exist with the same size are skipped (so
re-runs are cheap). The index page is always regenerated.
"""

from __future__ import annotations

import argparse
import re
import shutil
from collections import defaultdict
from pathlib import Path


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


_FILENAME_RE = re.compile(r"^(?P<district>.+?)-(?P<year>\d{4})\.pdf$", re.IGNORECASE)


def parse_filename(name: str) -> tuple[str, int] | None:
    m = _FILENAME_RE.match(name)
    if not m:
        return None
    return m.group("district").strip(), int(m.group("year"))


def render_index(by_district: dict[str, list[tuple[int, str, int]]],
                 iccsd_key: str) -> str:
    """Render the docs/audited-financials/index.md."""
    out: list[str] = []
    out.append("---")
    out.append("title: Audited Financial Statements")
    out.append("---")
    out.append("")
    out.append("# Audited Financial Statements")
    out.append("")
    out.append(
        "Audited annual financial statements for the Iowa City Community "
        "School District and a panel of comparable Iowa districts. Use "
        "these for benchmarking ICCSD's financial position against peers "
        "with similar enrollment, geography, or funding structures."
    )
    out.append("")
    out.append("---")
    out.append("")

    # ICCSD first
    if iccsd_key in by_district:
        years = sorted(by_district[iccsd_key])
        out.append("## Iowa City Community School District")
        out.append("")
        out.append(
            "The district's audit backlog — flagged in 2026 press "
            "coverage as a driver of the bond rating loss and the bank "
            "loan rejection — is visible directly in this list. See "
            "[Topics → Budget](../topics/budget.md) for the broader arc."
        )
        out.append("")
        years_present = {y for y, _, _ in years}
        all_years = range(2020, 2026)
        bullets: list[str] = []
        for y in all_years:
            match = next(((yr, fn, sz) for yr, fn, sz in years if yr == y), None)
            if match:
                yr, fn, sz = match
                bullets.append(
                    f"- **FY{yr}** — [Audited Financial Statements]({fn}) "
                    f"({sz/1024/1024:.1f} MB)"
                )
            else:
                bullets.append(
                    f"- **FY{y}** — _not yet released_ (part of the 2026 "
                    f"audit-backlog story)"
                )
        out.extend(bullets)
        out.append("")

    # Peer districts
    peer_keys = sorted(k for k in by_district if k != iccsd_key)
    if peer_keys:
        out.append("## Peer districts (Iowa)")
        out.append("")
        out.append(
            f"{len(peer_keys)} peer Iowa districts, fiscal years 2020–2025 "
            f"where available."
        )
        out.append("")
        for district_key in peer_keys:
            years = sorted(by_district[district_key])
            # Convert key back to display name
            display = " ".join(part.capitalize() for part in district_key.split("-"))
            display = display.replace("Csd", "CSD")
            out.append(f"### {display}")
            out.append("")
            links = [
                f"[FY{yr}]({fn}) ({sz/1024/1024:.1f} MB)"
                for yr, fn, sz in years
            ]
            out.append("- " + " &nbsp;·&nbsp; ".join(links))
            out.append("")

    out.append("---")
    out.append("")
    out.append(
        "*Files in this directory are PDFs hosted on this site, not "
        "linked out to district websites. They were sourced from each "
        "district's official audited financial statement filings.*"
    )
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, required=True,
                    help="Folder containing the source PDFs")
    ap.add_argument("--out", type=Path, required=True,
                    help="docs/audited-financials/ directory")
    args = ap.parse_args()

    if not args.source.is_dir():
        print(f"ERROR: source not found: {args.source}")
        return 2
    args.out.mkdir(parents=True, exist_ok=True)

    by_district: dict[str, list[tuple[int, str, int]]] = defaultdict(list)
    iccsd_key = "iowa-city-csd"
    copied = 0
    skipped = 0

    for pdf in sorted(args.source.glob("*.pdf")):
        parsed = parse_filename(pdf.name)
        if not parsed:
            print(f"  skip (unparsed name): {pdf.name}")
            continue
        district, year = parsed
        district_key = slugify(district)
        out_name = f"{district_key}-{year}.pdf"
        out_path = args.out / out_name

        # Idempotency: skip if size matches
        if out_path.exists() and out_path.stat().st_size == pdf.stat().st_size:
            skipped += 1
        else:
            shutil.copy2(pdf, out_path)
            copied += 1

        by_district[district_key].append((year, out_name, out_path.stat().st_size))

    print(f"Audited financials: {copied} copied, {skipped} already current.")
    print(f"Districts indexed: {len(by_district)}")

    idx = render_index(by_district, iccsd_key)
    (args.out / "index.md").write_text(idx, encoding="utf-8", newline="\n")
    print(f"Wrote {args.out / 'index.md'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
