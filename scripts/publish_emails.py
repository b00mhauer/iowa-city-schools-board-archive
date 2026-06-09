"""Generate docs/emails/index.md from the PDFs already in docs/emails/.

The user dumps email-archive PDFs into docs/emails/ directly (typically
exported from Google Vault via a public-records request or similar
process). This script reads what's there, categorizes by keyword in the
filename, and emits a navigable index page grouped by topic.

Filenames typically follow the pattern:
    KP Google Vault - <Subject Line>.pdf
    KP Google Vault - <Subject Line>_Redacted.pdf

We strip the "KP Google Vault - " prefix when displaying titles. The
underlying filenames (with all their odd characters) become the URL
targets unchanged so the PDFs resolve cleanly on GitHub Pages.

Idempotent: re-running with no new files just regenerates the same
index. Categorization rules are evaluated in order — first match wins.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote


# Display prefix to strip from filenames when rendering titles.
TITLE_PREFIX = "KP Google Vault - "

# Categorization rules — (display name, list of case-insensitive keyword
# fragments). First match wins; order from most-specific to most-generic.
# Rules are evaluated in order; first match wins. ALL specific categories
# run before the catch-all "Audit — other" so that, e.g., a file named
# "Audit - OUTGOING TRANSFER PERSHING LLC $4,000,000.pdf" lands under
# Outgoing transfers (its substantive topic), not the Audit catch-all.
CATEGORIES: list[tuple[str, list[str]]] = [
    ("Bond rating, investors, and credit agencies", [
        "bond rating", "Moody", "Nuveen", "bondholder", "rating withdrawal",
        "Truist Gove", "Key Government Finance", "GO Bond",
        "SAVE Bond", "Continuing Disclosure",
        # debt-history and projections requests are typically investor-facing
        "Debt History", "Debt Projections",
    ]),
    ("Outgoing transfers, fund movements, and large transactions", [
        "PERSHING", "OUTGOING", "OUTGO",
        "TRANSFER", "Outgo",
        # banking / treasury operational changes that move fund flows
        "New Account Number", "Account Number",
    ]),
    ("SBRC and state oversight", [
        "SBRC", "School Budget Review Committee",
        "School Accounting System reporting",
        "FY 2026 School Budget System",
    ]),
    ("Compliance, grants, and federal reporting", [
        "Compliance Related", "Perkins V", "Perkins Claim", "Perkins",
        "IDEA Part B", "Iowa Grants", "Assurances",
        "Iowa Department o", "Iowa Department of",
    ]),
    ("Open Enrollment", [
        "Open Enrollment", "Concurrent Enr",
    ]),
    ("Construction, contracts, and asset commitments", [
        "Construction Commitments", "Construction Confirmation",
        "Larson Construction", "Touch Point", "DDI Leasing",
        "Capital Asset Suralink", "Fixed Assets", "Capital Projects Wants",
        # additional catches: Suralink alone, Commitments Detail,
        # priority-setting docs, district trailers as a capital asset
        "Suralink", "Commitments Detail", "Wants v. Needs", "Wants v Needs",
        "Trailers",
    ]),
    ("Vendor and operational requests", [
        "Hillyard", "Big Iron Welding", "Sewing Machines", "Frontline Analytics",
        "Hardware Break-Fix", "Vista Software", "Delta Dental",
        "Heat Pump Equipment", "Dream Accelerator",
        # food service, employee-benefit ops, UEN job-aid feedback
        "Food Srv", "EMP benefit", "CAR Inquir",
        "UEN-Job", "UEN Job", "Job Aid", "JobAid",
        # district-side vendor payments
        "Additional Cost Payment", "Cost Payment received",
    ]),
    ("Personnel, hiring, and HR", [
        "Letter of Recommendation",
        "Director of Financial Reporting",
        "New Director of Financial",
        "Job Application", "Job application",
    ]),
    ("Real estate, appraisals, and property dispositions", [
        "Appraisal Request", "Appraisal",
        "Real Estate", "Real Property",
    ]),
    ("Professional associations and peer networking", [
        "IASBO", "ASBO ",
        "Region 7",
    ]),
    ("Auditor relationships and engagements", [
        "Auditing Services", "Barr & Company", "Barr ", "RSM", "New Iowa Auditors",
        "Contact for accountant", "Transmittal letter", "Tranmittal letter",
    ]),
    ("Audit delay, status, and items", [
        "Audit Delay", "Audit Update", "Audit Status", "Audit Check",
        "Audit Inquiry", "Audit Request", "Audit Items", "Audit responses",
        "Audit question", "audit extension",
        "FY23", "FY24", "FYE 6_30_2023", "2023 & 2024 Audits",
        # audit-prep workpapers and supporting deliverables
        "Cash Account reconciliation", "JE uploaded", "new JE",
        "Excel Report and new JE", "Draft ETA",
    ]),
    ("Audit — other", [
        "Audit",
    ]),
    ("Calendar invites and meetings", [
        "Accepted_",
    ]),
    ("Out-of-office and routine replies", [
        "Out of Office", "Out of the Office",
        # very short, content-free routine replies
        "Thank you!", "Help please",
    ]),
]


def clean_title(filename: str) -> str:
    """Strip the Google Vault prefix and clean up underscores."""
    stem = filename
    if stem.lower().endswith(".pdf"):
        stem = stem[:-4]
    if stem.startswith(TITLE_PREFIX):
        stem = stem[len(TITLE_PREFIX):]
    stem = stem.replace("_", " ").strip()
    return stem


def categorize(filename: str) -> str:
    name_lower = filename.lower()
    for category, keywords in CATEGORIES:
        for kw in keywords:
            if kw.lower() in name_lower:
                return category
    return "Other / uncategorized"


def is_redacted(filename: str) -> bool:
    return "redacted" in filename.lower()


def render_index(by_cat: dict[str, list[tuple[str, str, int]]]) -> str:
    out: list[str] = []
    out.append("---")
    out.append("title: Email Archive")
    out.append("---")
    out.append("")
    out.append("# Email Archive")
    out.append("")
    out.append(
        "Email correspondence relating to the ICCSD audit backlog, bond "
        "rating, fund management, and related financial topics, exported "
        "from Google Vault. Documents are grouped by topical category "
        "based on subject-line keywords."
    )
    out.append("")

    total = sum(len(v) for v in by_cat.values())
    redacted_count = sum(
        1 for entries in by_cat.values() for _, fn, _ in entries
        if is_redacted(fn)
    )
    out.append(
        f"**{total} documents** indexed; **{redacted_count}** have been "
        f"published in their redacted form. Some emails appear in both "
        f"redacted and unredacted versions; both are linked so readers "
        f"can compare what was withheld."
    )
    out.append("")
    out.append(
        "!!! warning \"Provenance and reading guide\""
    )
    out.append("")
    out.append(
        "    Subject lines and file names are the originals from the "
        "vault export; the site does not paraphrase or interpret them. "
        "Each entry below is a direct link to the PDF on this site. "
        "Where an email has been redacted before publication, it is "
        "marked **(Redacted)**; otherwise it is the unredacted document "
        "as exported."
    )
    out.append("")

    # Category ordering: anchor key topics at the top, then everything else
    # alphabetical, with "Other" last.
    preferred_order = [c for c, _ in CATEGORIES]
    other_last = "Other / uncategorized"
    seen: set[str] = set()
    ordered_cats: list[str] = []
    for c in preferred_order:
        if c in by_cat and c not in seen:
            ordered_cats.append(c)
            seen.add(c)
    for c in sorted(by_cat.keys()):
        if c not in seen and c != other_last:
            ordered_cats.append(c)
            seen.add(c)
    if other_last in by_cat:
        ordered_cats.append(other_last)

    for category in ordered_cats:
        entries = sorted(by_cat[category], key=lambda e: e[0].lower())
        out.append(f"## {category}")
        out.append("")
        out.append(f"_{len(entries)} document{'s' if len(entries) != 1 else ''}._")
        out.append("")
        for title, filename, size_bytes in entries:
            redacted_mark = " **(Redacted)**" if is_redacted(filename) else ""
            href = quote(filename, safe="")
            size_kb = size_bytes / 1024
            size_str = (
                f"{size_kb/1024:.1f} MB" if size_kb >= 1024 else f"{size_kb:.0f} KB"
            )
            out.append(f"- [{title}]({href}) ({size_str}){redacted_mark}")
        out.append("")

    out.append("---")
    out.append("")
    out.append(
        "*Files are hosted directly on this site. To request a correction "
        "(wrong category, missing redaction, etc.), open an "
        "[issue](https://github.com/b00mhauer/iowa-city-schools-board-archive/issues).*"
    )
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", type=Path, required=True,
                    help="docs/emails/ directory")
    args = ap.parse_args()

    if not args.dir.is_dir():
        print(f"ERROR: not a directory: {args.dir}")
        return 2

    by_cat: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for p in sorted(args.dir.glob("*.pdf")):
        category = categorize(p.name)
        by_cat[category].append((clean_title(p.name), p.name, p.stat().st_size))

    if not by_cat:
        print(f"No PDFs found in {args.dir}; nothing to do.")
        return 0

    idx_md = render_index(by_cat)
    (args.dir / "index.md").write_text(idx_md, encoding="utf-8", newline="\n")

    total = sum(len(v) for v in by_cat.values())
    print(f"Indexed {total} email PDFs across {len(by_cat)} categor"
          f"{'ies' if len(by_cat) != 1 else 'y'}.")
    for c in sorted(by_cat, key=lambda k: -len(by_cat[k])):
        print(f"  {len(by_cat[c]):3d}  {c}")
    print(f"Wrote {args.dir / 'index.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
