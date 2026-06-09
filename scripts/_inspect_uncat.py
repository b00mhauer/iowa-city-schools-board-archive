"""One-off: dump filenames currently landing in Other / uncategorized."""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from publish_emails import categorize  # noqa: E402

EMAILS = HERE.parent / "docs" / "emails"

buckets: dict[str, list[str]] = {}
for name in sorted(os.listdir(EMAILS)):
    if not name.lower().endswith(".pdf"):
        continue
    buckets.setdefault(categorize(name), []).append(name)

print("Category sizes:")
for cat in sorted(buckets, key=lambda c: -len(buckets[c])):
    print(f"  {len(buckets[cat]):3d}  {cat}")

print()
print("=== Other / uncategorized filenames ===")
for name in buckets.get("Other / uncategorized", []):
    print(name)
