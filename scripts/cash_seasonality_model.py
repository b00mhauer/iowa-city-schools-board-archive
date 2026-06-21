"""Monte-Carlo liquidity model for the ICCSD General Fund.

Question it answers: for a balance held at the END of each month, how many
days of cash on hand are needed to have a 95% / 99% / 99.9% chance of NOT
running the General Fund dry (cash < $0, i.e. needing an emergency interfund
loan or anticipatory warrant) at any point in the following 12 months?

Method (a first-passage / ruin calculation):
  - Each forward month's net OPERATING cash flow is modeled as
        X_j = mu_j + N(0, sigma)
    where mu_j is the deterministic seasonal mean and sigma is monthly
    flow volatility (independent across months).
  - From a given starting month we simulate the next 12 monthly flows,
    accumulate them, and take the running minimum of the path (the deepest
    point relative to the starting balance).
  - The balance needed for confidence p is the negative of the p-lower
    quantile of that running minimum: B*(p) = -quantile(runmin, 1-p).
  - Converted to "days cash on hand" at the district/PFM operating
    convention of ~$610,000/day (~$223M FY26 GF operating spend / 365).

INPUTS — read these caveats before trusting the numbers:
  * mu_j are FY26 cash-basis operating flows (revenues minus expenditures,
    EXCLUDING interfund loans and warrant proceeds), derived from PFM's
    April 28, 2026 "Exhibit 1a" General Fund monthly cash-flow schedule.
    This is the only clean cash-basis year available; FY24/FY25 audits are
    still outstanding.
  * sigma is an ASSUMPTION, not an estimate. With ~1 clean year of monthly
    data it cannot be fit with confidence. The base case ($2.5M) reflects
    ordinary month-to-month timing noise; a conservative case ($4.0M) is
    consistent with the dispersion seen between the FY25 and FY26 summer
    drawdowns. Swap in a better sigma once reconciled history exists.
  * Independence across months makes far-horizon variance grow with
    sqrt(n). Real seasonal-timing noise is partly mean-reverting, so the
    high-confidence requirements for FALL/WINTER starts (whose binding
    trough is the following September, ~6-11 months out) are the least
    reliable. Spring/early-summer starts (trough 1-5 months out) are most
    reliable.
  * Balances are month-END. The true within-month low (mid-month payroll
    before late-month tax/aid receipts) is lower, so add a few days of
    buffer for intra-month timing.
"""

from __future__ import annotations

import numpy as np

MONTHS = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
          "Jan", "Feb", "Mar", "Apr", "May", "Jun"]

# FY26 cash-basis operating net flows by month ($), from PFM Exhibit 1a.
MU = np.array([
    -9_928_258, -13_416_091, -895_687, 28_899_706, -2_256_184, -5_379_096,
    -6_778_899, -3_409_798, -1_960_135, 22_856_394, -670_255, -6_467_753,
], dtype=float)

DOLLARS_PER_DAY = 610_000.0  # GF operating spend per day (PFM convention)

CONFIDENCE = [("50%", 0.50), ("95%", 0.95), ("99%", 0.99), ("99.9%", 0.999)]


def required_days(sigma_month: float, n_paths: int = 400_000, seed: int = 1):
    """Return {month: {conf: days}} required to survive the next 12 months."""
    rng = np.random.default_rng(seed)
    table: dict[str, dict[str, float]] = {}
    for start in range(12):
        fwd = [(start + 1 + k) % 12 for k in range(12)]
        means = MU[fwd]
        eps = rng.normal(0.0, sigma_month, size=(n_paths, 12))
        cum = np.cumsum(means[None, :] + eps, axis=1)
        runmin = cum.min(axis=1)
        row = {}
        for label, p in CONFIDENCE:
            dollars = -np.percentile(runmin, (1 - p) * 100)
            row[label] = max(dollars, 0.0) / DOLLARS_PER_DAY
        table[MONTHS[start]] = row
    return table


def print_table(sigma_month: float) -> None:
    table = required_days(sigma_month)
    print(f"\nsigma = ${sigma_month/1e6:.1f}M/month   "
          f"(days of GF cash needed at each month-end)")
    print(f"{'End of':>7} | " + " | ".join(f"{c:>6}" for c, _ in CONFIDENCE))
    for mo in MONTHS:
        row = table[mo]
        print(f"{mo:>7} | " + " | ".join(f"{row[c]:6.0f}" for c, _ in CONFIDENCE))


if __name__ == "__main__":
    for s in (1.5e6, 2.5e6, 4.0e6):
        print_table(s)
