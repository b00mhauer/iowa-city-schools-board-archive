---
title: "General Fund cash seasonality & liquidity risk"
---

<div class="rating-hero" markdown>

<div class="eyebrow">IOWA CITY SCHOOLS · LIQUIDITY ANALYSIS</div>

<div class="hero-title">Reading the General Fund cash balance against its season</div>

ICCSD's General Fund cash balance swings by more than **$30 million** within a single year — not because the district is getting richer or poorer month to month, but because property taxes and state aid arrive in a few large, predictable lumps while payroll goes out evenly. This page establishes a baseline seasonal pattern from the district's own monthly cash-flow schedules and shows how to judge whether a given balance — say, *30 days cash on hand in June* — is low, adequate, or comfortable **for that time of year**.

</div>

!!! warning "Unofficial community analysis"

    This page is independent analysis prepared by an ICCSD community member, built from the district's published board materials. It is **not** produced by the district, PFM Financial Advisors, or the Financial Oversight Committee. The underlying monthly figures are *unaudited* cash-flow projections and internal records; with the FY24 and FY25 audits still outstanding, even the beginning cash balances were described by PFM as "unknown variables." Treat the *shape* of the seasonality as reliable and the *exact dollar levels* as provisional.

## The short answer

<div class="stat-cards" markdown>

<div class="stat-card danger" markdown>
<div class="stat-value">Aug–Sep</div>
<div class="stat-label">The annual cash trough. Before October property taxes arrive, the General Fund runs dry — FY26 needed a $10M interfund loan just to stay positive.</div>
</div>

<div class="stat-card success" markdown>
<div class="stat-value">Oct & Apr</div>
<div class="stat-label">The two annual peaks. Iowa property-tax settlements (~$34M in October, ~$30M in April) refill the account in a single month.</div>
</div>

<div class="stat-card info" markdown>
<div class="stat-value">~30 days</div>
<div class="stat-label">A June balance of ~30 days cash is <strong>adequate but tight</strong> — right at the floor the district steers to, enough for July payroll with almost no cushion.</div>
</div>

</div>

## Why the General Fund is seasonal

The district laid out the mechanics plainly at the February 10, 2026 Financial Oversight Committee meeting:

- **Property taxes arrive twice a year.** Local property-tax settlements land in **October and April** and together total roughly **$90 million across all funds** (about **$34M** and **$30M** of that flows to the General Fund). These two months are the only times the account is materially refilled.
- **State aid is steady — until FY27.** State foundation aid pays in **~$10 million monthly installments, September through June** (FY26 regime). Beginning **FY27 it moves to quarterly** payments (~$26.5M in August, November, February, and May), which reshapes the trough months — more on that below.
- **Payroll is flat and relentless.** General Fund payroll and benefits run **~$16 million every month**, rising to **~$19M in June** as the fiscal year closes. It does not wait for the tax cycle.

Put those together and the balance has a fixed annual rhythm: it **draws down steadily between tax settlements**, craters in the late summer before October taxes, dips again in late winter before April taxes, and spikes the month each settlement lands.

## The baseline pattern (FY 2025-26)

This is the cleanest near-complete year of monthly data — actual through March 2026, projected through June, from PFM's adopted "Option 1" schedule. Days cash on hand uses the district/PFM operating convention of roughly **$610,000 per day** (≈ FY26 General Fund operating expenditures of ~$223M ÷ 365).

| Month-end | Ending GF cash | Days cash on hand | Seasonal index¹ | Read |
|---|---:|---:|---:|---|
| Jul 2025 | $9.4M | 15 | 0.45 | Draining |
| **Aug 2025** | **$6.0M** | **10** | **0.29** | 🔴 Trough (incl. $10M loan) |
| **Sep 2025** | **$5.1M** | **8** | **0.25** | 🔴 Annual low |
| Oct 2025 | $34.0M | 56 | 1.64 | 🟢 Property-tax peak |
| Nov 2025 | $31.8M | 52 | 1.53 | 🟢 High |
| Dec 2025 | $26.4M | 43 | 1.27 | Comfortable |
| Jan 2026 | $19.6M | 32 | 0.94 | Draining |
| Feb 2026 | $16.2M | 27 | 0.78 | Low |
| Mar 2026 | $14.2M | 23 | 0.69 | 🟠 Winter trough |
| Apr 2026 | $37.1M | 61 | 1.79 | 🟢 Property-tax peak |
| May 2026 | $27.8M | 46 | 1.34 | Comfortable |
| Jun 2026 | $21.4M | 35 | 1.03 | Year-end floor |

¹ *Seasonal index = that month's ending balance ÷ the 12-month average ($20.8M). 1.00 = an average month; 0.25 = a quarter of the average; 1.79 = nearly double.*

<div class="chart-block">
<svg viewBox="0 0 770 360" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:auto;font-family:system-ui,sans-serif">
  <style>
    .cs-axis { stroke: #6b7280; stroke-width: 1.5; }
    .cs-grid { stroke: #e5e9f0; stroke-width: 1; }
    .cs-lbl { font-size: 11px; fill: #4b5563; }
    .cs-title { font-size: 13px; fill: #1f2937; font-weight: 700; }
    .cs-line { fill: none; stroke: #2c5fa1; stroke-width: 2.5; }
    .cs-dot { fill: #2c5fa1; }
    .cs-peak { fill: #1e7a3a; }
    .cs-trough { fill: #b03a2e; }
    .cs-floor { stroke: #b03a2e; stroke-width: 1.5; stroke-dasharray: 6 4; fill: none; }
    .cs-floor-lbl { font-size: 10.5px; fill: #b03a2e; font-weight: 600; }
    .cs-note { font-size: 10.5px; font-weight: 700; }
    .cs-summer { fill: rgba(176, 58, 46, 0.06); }
  </style>

  <text x="20" y="20" class="cs-title">General Fund ending cash by month — FY 2025-26 ($M)</text>

  <!-- summer drawdown band (May -> Sep) -->
  <rect x="660" y="40" width="59" height="260" class="cs-summer"/>
  <rect x="70" y="40" width="118" height="260" class="cs-summer"/>

  <!-- y grid + axis -->
  <line x1="60" y1="40" x2="60" y2="300" class="cs-axis"/>
  <line x1="60" y1="300" x2="730" y2="300" class="cs-axis"/>
  <line x1="60" y1="40"  x2="730" y2="40"  class="cs-grid"/>
  <line x1="60" y1="105" x2="730" y2="105" class="cs-grid"/>
  <line x1="60" y1="170" x2="730" y2="170" class="cs-grid"/>
  <line x1="60" y1="235" x2="730" y2="235" class="cs-grid"/>
  <text x="54" y="304" class="cs-lbl" text-anchor="end">$0</text>
  <text x="54" y="239" class="cs-lbl" text-anchor="end">$10</text>
  <text x="54" y="174" class="cs-lbl" text-anchor="end">$20</text>
  <text x="54" y="109" class="cs-lbl" text-anchor="end">$30</text>
  <text x="54" y="44"  class="cs-lbl" text-anchor="end">$40</text>

  <!-- ~30-day July-payroll floor -->
  <line x1="60" y1="181" x2="730" y2="181" class="cs-floor"/>
  <text x="726" y="177" class="cs-floor-lbl" text-anchor="end">~30-day floor (covers one July payroll)</text>

  <!-- data line -->
  <polyline points="70,239 129,261 188,267 247,79 306,94 365,129 424,173 483,195 542,207 601,59 660,119 719,161" class="cs-line"/>

  <circle cx="70"  cy="239" r="4" class="cs-dot"/>
  <circle cx="129" cy="261" r="4" class="cs-dot"/>
  <circle cx="188" cy="267" r="5" class="cs-trough"/>
  <circle cx="247" cy="79"  r="5" class="cs-peak"/>
  <circle cx="306" cy="94"  r="4" class="cs-dot"/>
  <circle cx="365" cy="129" r="4" class="cs-dot"/>
  <circle cx="424" cy="173" r="4" class="cs-dot"/>
  <circle cx="483" cy="195" r="4" class="cs-dot"/>
  <circle cx="542" cy="207" r="5" class="cs-trough"/>
  <circle cx="601" cy="59"  r="5" class="cs-peak"/>
  <circle cx="660" cy="119" r="4" class="cs-dot"/>
  <circle cx="719" cy="161" r="4" class="cs-dot"/>

  <text x="247" y="72"  class="cs-note" fill="#1e7a3a" text-anchor="middle">Oct tax</text>
  <text x="601" y="52"  class="cs-note" fill="#1e7a3a" text-anchor="middle">Apr tax</text>
  <text x="188" y="285" class="cs-note" fill="#b03a2e" text-anchor="middle">Sep low</text>
  <text x="542" y="225" class="cs-note" fill="#b03a2e" text-anchor="middle">Mar dip</text>

  <!-- x labels -->
  <text x="70"  y="316" class="cs-lbl" text-anchor="middle">Jul</text>
  <text x="129" y="316" class="cs-lbl" text-anchor="middle">Aug</text>
  <text x="188" y="316" class="cs-lbl" text-anchor="middle">Sep</text>
  <text x="247" y="316" class="cs-lbl" text-anchor="middle">Oct</text>
  <text x="306" y="316" class="cs-lbl" text-anchor="middle">Nov</text>
  <text x="365" y="316" class="cs-lbl" text-anchor="middle">Dec</text>
  <text x="424" y="316" class="cs-lbl" text-anchor="middle">Jan</text>
  <text x="483" y="316" class="cs-lbl" text-anchor="middle">Feb</text>
  <text x="542" y="316" class="cs-lbl" text-anchor="middle">Mar</text>
  <text x="601" y="316" class="cs-lbl" text-anchor="middle">Apr</text>
  <text x="660" y="316" class="cs-lbl" text-anchor="middle">May</text>
  <text x="719" y="316" class="cs-lbl" text-anchor="middle">Jun</text>

  <text x="395" y="340" class="cs-lbl" text-anchor="middle">Shaded = late-summer drawdown leg (April peak spends down to the September trough).</text>
</svg>
</div>

The August–September figures come with an asterisk that *strengthens* the point: those balances **already include the $10 million interfund loan** the district drew from its health-insurance fund in August 2025. Without it, the General Fund would have ended August and September roughly **$4 million in the red**. The natural, unborrowed low point of the year is deeply negative — which is exactly why the district borrows every late summer.

## The flow pattern repeats (FY 2024-25)

We only have one full year of *reconstructed monthly balances*, but the FY25 monthly receipts and disbursements (from the Q3 report) confirm the **same seasonal shape** in the underlying flows — large positive months in October and April, persistent ~$5M monthly deficits in between, and a deep negative in June as the year closes:

| | Jul | Aug | Sep | **Oct** | Nov | Dec | Jan | Feb | Mar | **Apr** | May | Jun |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| FY25 net flow ($M) | −2.6 | −5.5 | −4.5 | **+30.0** | −5.8 | +1.7 | −6.7 | −6.0 | −2.5 | **+25.4** | −1.6 | −22.1 |

The two tax months (+$30M, +$25M) and the steady between-settlement bleed are structural, not one-offs. That is what makes a *baseline* meaningful in the first place.

## The catch: FY27 changes the season

The shift of state aid to **quarterly** payments starting FY27 is the single biggest reason a naive seasonal index built on FY26 will mislead you going forward. With a large state-aid payment now landing in **August**, the dangerous late-summer gap shortens — but a **new, deeper trough opens in March**, between the February and May aid payments:

| Month-end | FY26 ending cash | FY27 ending cash | What changed |
|---|---:|---:|---|
| Aug | $6.0M | $13.4M | 🟢 Aug state-aid payment cushions the summer |
| Sep | $5.1M | $9.9M | Less acute |
| Jan | $19.6M | $10.1M | 🟠 No monthly aid; spending down |
| **Mar** | $14.2M | **$6.3M** | 🔴 New annual trough (Feb→May aid gap) |
| Jun | $21.4M | $18.3M | Year-end floor, ~30 days |

**Implication for your hypothesis:** a single year is enough to read the *mechanism*, but the trough *month* is not stationary — it migrates from September (FY26) toward March (FY27) as the payment calendar changes. A liquidity model has to track the **payment calendar**, not just the month name.

## Judging a balance: the forward-drawdown test

Here is the core of your hypothesis, made precise. The right question is **not** "is this balance above or below the seasonal average?" It is:

> **Will the balance survive the largest drawdown still ahead before the next big inflow — without dropping below the operating floor?**

The operating floor is roughly **one month of payroll (~$16–19M)** plus whatever minimum buffer the board wants; below it, the district cannot make payroll between inflows and must borrow (interfund loan or anticipatory warrant). The two drawdown "legs" that bind are:

<div class="gap-bar" markdown>
<div class="gap-label"><strong>Summer leg — April peak → late-summer trough</strong><span>FY26: $37.1M → $5.1M = −$32M over 5 months (≈ −$42M before the $10M loan)</span></div>
<div class="gap-track">
  <div class="gap-fill" style="width: 86%; background:#b03a2e;"></div>
</div>
</div>

<div class="gap-bar" markdown>
<div class="gap-label"><strong>Winter leg — October peak → late-winter trough</strong><span>FY26: $34.0M → $14.2M = −$20M over 5 months</span></div>
<div class="gap-track">
  <div class="gap-fill" style="width: 53%; background:#d98a2b;"></div>
</div>
</div>

A practical rule for any month *m*:

> **Liquidity-safe if:  starting cash ≥ (worst cumulative net outflow from month *m* to the next major inflow)  +  (minimum operating floor).**

The same dollar balance is therefore safe in one month and dangerous in another, because what's *ahead* differs:

| If you're holding ~$18M (≈30 days)… | …entering this month | Verdict |
|---|---|---|
| $18M | **June** | 🟡 Adequate — only July's gap to bridge before August aid |
| $18M | **September** | 🟢 Comfortable — October taxes are days away |
| $18M | **December** | 🟠 Thin — the Jan–Mar bleed is ahead of you |
| $18M | **April (post-tax)** | 🔴 Alarming — you should be near $37M; the whole summer leg is ahead |

That is precisely why "30 days" cannot be judged without a month attached.

## So: is 30 days in June low, adequate, or high?

**Adequate, but at the floor — not comfortable.** Three reasons:

1. **June is the year-end handoff balance.** Its only job is to carry the district through **July** — one payroll — until the next inflow. In the FY27 regime that next inflow is the **August quarterly state-aid payment** (~$26.5M), so the forward drawdown from June 30 is relatively short. The district's own advisors size the June-30 target to exactly this: PFM calls **35 days "sufficient to make July payroll,"** **30 days** still sufficient, and **18 days "NOT sufficient to make July payroll."** Thirty days sits just above the line that fails.

2. **It is the bottom of the comfortable band, not the middle.** The summer leg is the binding constraint of the whole year. Going *into* it with 30 days leaves essentially no cushion for a bad July or a delayed payment — it works only if the next six weeks are clean.

3. **It is thin by any external yardstick.** Thirty days is ~8% of annual operating spending. Rating-agency "available reserves" benchmarks for an A/A+ Iowa district sit near **17% of revenue**; ICCSD's full-year reserves are already only ~9.5%. Thirty days of *cash* in June is consistent with a district operating with little margin — fine if managed tightly, fragile to any shock.

**Bottom line:** 30 days in June is a *passing* grade, not a *strong* one. The same 30 days in April would be a red flag; in September it would be reassuring.

## Putting a probability on it: required cushion by month

The deterministic test above answers "what's the *expected* worst point." Adding the *variability* of the flows turns it into a probability — exactly as you'd expect. Model each forward month's net operating flow as a random draw, **flow = seasonal mean (μ) + noise (σ)**; the cash path is then a seasonal random walk, and "running dry in the next 12 months" is the chance its *running minimum* falls below zero (a [first-passage / ruin problem](https://en.wikipedia.org/wiki/First-hitting-time_model)). The balance needed for confidence *p* is:

> **Required balance(month) ≈ (mean forward drawdown to the binding trough) + z<sub>p</sub> × (σ of that drawdown)**, with z = **1.645** (95%), **2.326** (99%), **3.090** (99.9%).

The table below is that calculation run as a 400,000-path Monte Carlo from each month-end, using the FY26 cash-basis operating flows as μ and a **$2.5M/month** flow volatility as the base case. It reports the **days of cash on hand** a balance must clear to have a given chance of *not* needing an emergency loan or warrant over the next 12 months. (Reproduce or re-run with your own σ: [`scripts/cash_seasonality_model.py`](https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/scripts/cash_seasonality_model.py).)

| Balance held at end of… | 50% (mean) | **95%** | **99%** | **99.9%** | Binding trough |
|---|---:|---:|---:|---:|---|
| Jul | 24 | 34 | 39 | 46 | upcoming Sep (near) |
| Aug | 4 | 22 | 32 | 43 | next Sep (far) |
| Sep | 0 | 23 | 32 | 43 | next Sep (far) |
| Oct | 47 | 69 | 78 | 88 | next Sep (far) |
| Nov | 44 | 64 | 73 | 83 | next Sep (far) |
| Dec | 35 | 55 | 63 | 72 | next Sep (far) |
| Jan | 24 | 42 | 50 | 59 | next Sep (far) |
| Feb | 18 | 36 | 43 | 51 | upcoming Sep |
| Mar | 15 | 31 | 38 | 46 | upcoming Sep |
| Apr | 53 | 67 | 74 | 82 | upcoming Sep (near) |
| May | 51 | 65 | 71 | 78 | upcoming Sep (near) |
| **Jun** | **41** | **52** | **57** | **64** | upcoming Sep (near) |

*All figures are days of General Fund operating cash (≈ $610K/day). September is the **universal binding trough** — every starting month is ultimately tested against the late-summer low before October property taxes arrive.*

Three things to read off it:

- **The low-balance months are the low-risk months.** August and September need only ~22–23 days at 95% — *less* than June — because October's refill is imminent. The peak months (April, May, October) need the *most* (65–69 days) because from a peak you must self-fund the entire run down to the next trough. Required cushion tracks *forward drawdown*, not current level — your original point, now in numbers.
- **The near-trough rows are the trustworthy ones.** April–July starts are tested against the *upcoming* September (1–5 months out), where the model is on solid ground. The fall/winter rows are tested against the *following* September (6–11 months out); because the model assumes independent monthly noise, their high-confidence numbers are inflated (real seasonal-timing noise partly reverses month to month). Treat those as upper bounds.
- **σ is the swing input.** At a conservative **$4M/month** (consistent with the FY25-vs-FY26 summer-drawdown gap), every 95% figure rises ~10–18 days — June, for instance, goes from **52 → 62 days**. The *shape* of the table is robust; the *level* moves with σ.

### What this says about 30 days in June

The model puts hard numbers on the earlier verdict. To make June 30 genuinely safe *without* summer borrowing you'd want roughly:

<div class="stat-cards" markdown>

<div class="stat-card" markdown>
<div class="stat-value">~41 days</div>
<div class="stat-label">50/50 — the expected worst case (the Aug–Sep trough) just reaches $0.</div>
</div>

<div class="stat-card info" markdown>
<div class="stat-value">~52 days</div>
<div class="stat-label">95% confidence of clearing the summer with no loan or warrant.</div>
</div>

<div class="stat-card success" markdown>
<div class="stat-value">~64 days</div>
<div class="stat-label">99.9% — effectively never short over the next 12 months.</div>
</div>

</div>

So **30 days in June is well below even the coin-flip (~41-day) threshold** for self-funding the summer — which is exactly why the district draws an interfund loan or warrant every late summer. Thirty days isn't sized to *avoid* borrowing; it's sized to make *July* payroll and then borrow for August–September. Read against this table, ~30 days in June corresponds to a *high* probability of needing the summer backstop — consistent with what actually happened in FY26.

### Caveats (so the table isn't over-trusted)

- **One clean year of μ, an assumed σ.** FY24/FY25 audits are still open; PFM flagged even beginning cash as an "unknown variable." The means come from a single cash-basis year (partly projected) and σ is an assumption, not an estimate.
- **A moving calendar.** The FY27 shift of state aid to quarterly payments relocates the trough (Sep → March); the μ vector should be re-cut for FY27+ before applying the table forward.
- **Month-end, not intra-month.** The true low is mid-month (payroll before late-month receipts), so add a few days of buffer.
- **Floor = $0.** If the board wants a standing minimum buffer above zero, add it to every cell.

The honest upgrade path: once three-plus years of *reconciled* monthly balances exist, estimate σ (and its seasonal/serial structure) from data instead of assuming it, and the same script returns calibrated probabilities rather than well-reasoned estimates.

**Component refinement.** A first step down that path is already in the repo: [`scripts/cash_seasonality_components.py`](https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/scripts/cash_seasonality_components.py) replaces the single assumed σ with one built from the volatility of each flow *component* — letting the ~85% of the flow that is statutory/contractual (payroll, state aid, the property-tax *amount*) contribute almost no forecast error, and concentrating uncertainty in the lumpy "other local/federal" residual plus property-tax *timing*. It tightens the table by roughly 5 days (June 95%: 52 → **47 days**) and is more defensible, though still bounded by the same data-quality limits.

## Why the target is 60–90 days

Read across the table, the binding months — the post-tax peaks, which must self-fund the entire run down to the next trough — require **~60–76 days** at 95–99% confidence. A single reserve policy has to satisfy the most demanding month, which is exactly why a healthy target lands at **60 days (minimum) to 90 days (prudent)**, even though ICCSD currently steers to ~20–35. A standalone, self-contained visual explainer of this — built for sharing — lives at **[why-cash-reserve-targets.html](why-cash-reserve-targets.html)** (generated by [`scripts/make_reserve_onepager.py`](https://github.com/b00mhauer/iowa-city-schools-board-archive/blob/main/scripts/make_reserve_onepager.py)).

## Sources

- **ICCSD Board of Education.** [Capital Outlay Borrowing Need Memo Update for 4/1](https://simbli.eboardsolutions.com/SB_Meetings/ViewMeeting.aspx?S=36031992&MID=29357) (Curt Pratt, COO), April 1, 2026 work session. Source for the FY26–FY28 days-cash narrative and the interfund-loan history.
- **PFM Financial Advisors LLC.** *Year-to-Date General Fund Fiscal Progress & Update Regarding the Need to Issue Warrants*, presented [April 28, 2026](https://simbli.eboardsolutions.com/Meetings/Attachment.aspx?S=36031992&AID=566782&MID=28495) and [May 12, 2026](https://simbli.eboardsolutions.com/Meetings/Attachment.aspx?S=36031992&AID=569351&MID=29980). Source for the monthly General Fund cash-flow schedules (Exhibits 1a–2c) and the 18 / 30 / 35-day payroll thresholds.
- **ICCSD Business Services.** [Third Quarter Financial Report, FY2026 (Financials as of 3/31/26)](https://simbli.eboardsolutions.com/Meetings/Attachment.aspx?S=36031992&AID=569770&MID=29980), May 12, 2026. Source for FY25 and FY26 monthly revenues and expenditures and quarter-end cash/investment balances.
- **ICCSD.** [District Financial Update — Financial Oversight Committee](https://simbli.eboardsolutions.com/Meetings/Attachment.aspx?S=36031992&AID=512711&MID=27354), February 10, 2026. Source for the structural drivers (October/April property taxes ≈ $90M; ~$10M monthly state aid).
- **PFM Financial Advisors LLC.** [Iowa City CSD SAVE Cash Flow Analysis as of 6/4/2026](https://simbli.eboardsolutions.com/Meetings/Attachment.aspx?S=36031992&AID=579295&MID=29982), June 9, 2026. Source for the multi-year fund-level cash trajectory.

---

*Independent analysis. Not produced by ICCSD, PFM, or the Financial Oversight Committee. Built from unaudited board materials; figures will firm up as the FY24 and FY25 audits are completed. Spot a methodology issue or have a better data series? Open an [issue](https://github.com/b00mhauer/iowa-city-schools-board-archive/issues).*
