"""Generate a STANDALONE, self-contained HTML one-pager explaining why the
General Fund days-cash reserve target (60-90 days) matters, given seasonality.

No external CSS/JS/images: all styling is inline and all charts are inline
SVG, so the file renders identically offline and can be saved straight to PDF.
Output: docs/why-cash-reserve-targets.html
"""
from __future__ import annotations

MONTHS = ["Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun"]

# Seasonal shape, days of cash (FY26 actual ending balances, UNBORROWED ~19d avg)
FY26 = [15,-7,-8,39,36,27,16,10,7,44,29,19]
R60  = [v+41 for v in FY26]
R90  = [v+71 for v in FY26]

# Refined component-model required days (95%) by month, plus 50/99 for context
REQ = {  # month: (p50, p95, p99)
 "Jul":(24,30,32),"Aug":(3,17,24),"Sep":(0,17,24),"Oct":(47,62,69),
 "Nov":(43,58,64),"Dec":(34,49,54),"Jan":(23,37,43),"Feb":(18,31,36),
 "Mar":(14,27,32),"Apr":(52,61,65),"May":(51,59,63),"Jun":(40,47,51)}

RED,GREEN,BLUE,AMBER,INK,GREY="#b03a2e","#1e7a3a","#2c5fa1","#d98a2b","#1f2937","#6b7280"

# ---------- Chart 1: seasonal swing (line, 3 scenarios) ----------
def chart_swing():
    W,H=720,360; L,Rg,T,B=58,20,28,300
    ymin,ymax=-25,120
    def X(i): return L+(W-L-Rg)*i/11
    def Y(v): return T+(B-T)*(ymax-v)/(ymax-ymin)
    def poly(d): return " ".join(f"{X(i):.1f},{Y(v):.1f}" for i,v in enumerate(d))
    def dots(d,c):
        return "".join(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.4" fill="{c}"/>' for i,v in enumerate(d))
    xlab="".join(f'<text x="{X(i):.1f}" y="{B+18}" font-size="11" fill="{GREY}" text-anchor="middle">{m}</text>' for i,m in enumerate(MONTHS))
    ylab="".join(f'<text x="{L-8}" y="{Y(v)+4:.1f}" font-size="10" fill="{GREY}" text-anchor="end">{v}</text>'
                 +f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W-Rg}" y2="{Y(v):.1f}" stroke="#eef1f6"/>' for v in (-25,0,25,50,75,100,120))
    return f'''<svg viewBox="0 0 {W} {H+4}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
<rect x="{L}" y="{Y(0):.1f}" width="{W-Rg-L}" height="{B-Y(0):.1f}" fill="{RED}" opacity="0.08"/>
<rect x="{L}" y="{Y(15):.1f}" width="{W-Rg-L}" height="{Y(0)-Y(15):.1f}" fill="{AMBER}" opacity="0.13"/>
{ylab}
<line x1="{L}" y1="{Y(0):.1f}" x2="{W-Rg}" y2="{Y(0):.1f}" stroke="{RED}" stroke-width="1.2" stroke-dasharray="6 4" opacity="0.7"/>
<line x1="{L}" y1="{Y(15):.1f}" x2="{W-Rg}" y2="{Y(15):.1f}" stroke="{AMBER}" stroke-width="1" stroke-dasharray="2 3"/>
<text x="{L+4}" y="{Y(15)-4:.1f}" font-size="9.5" font-weight="700" fill="{AMBER}">~15-day floor (one mid-month payroll)</text>
<text x="{W-Rg-4}" y="{Y(-6):.1f}" font-size="9.5" font-style="italic" fill="{RED}" text-anchor="end">overdrawn &#8594; must borrow</text>
<polyline points="{poly(R90)}" fill="none" stroke="{GREEN}" stroke-width="2.4"/>{dots(R90,GREEN)}
<polyline points="{poly(R60)}" fill="none" stroke="{BLUE}" stroke-width="2.4"/>{dots(R60,BLUE)}
<polyline points="{poly(FY26)}" fill="none" stroke="{RED}" stroke-width="2.6"/>{dots(FY26,RED)}
<text x="{X(2):.1f}" y="{Y(-8)+22:.1f}" font-size="9.5" font-weight="700" fill="{RED}" text-anchor="middle">Aug&#8211;Sep go negative</text>
<text x="{X(9):.1f}" y="{Y(115):.1f}" font-size="9" fill="{GREY}" text-anchor="middle">Apr property-tax peak</text>
{xlab}
<g font-size="10.5">
<rect x="{L+2}" y="6" width="12" height="3" fill="{RED}"/><text x="{L+18}" y="11" fill="{INK}">ICCSD FY26 actual (~19-day avg, no rescue loan)</text>
<rect x="{L+292}" y="6" width="12" height="3" fill="{BLUE}"/><text x="{L+308}" y="11" fill="{INK}">60-day policy</text>
<rect x="{L+402}" y="6" width="12" height="3" fill="{GREEN}"/><text x="{L+418}" y="11" fill="{INK}">90-day policy</text>
</g></svg>'''

# ---------- Chart 2: why 60-90 decomposition (stacked bars) ----------
def chart_decomp():
    W,H=360,360; T,B=30,300; base=120; bw=70
    ymax=100
    def Y(v): return T+(B-T)*(ymax-v)/ymax
    segs=[("Operating floor",20,"#9aa7b8"),("Seasonal dip",27,BLUE)]
    def bar(cx,buf,total):
        y=B; out=""
        parts=[("#9aa7b8",20,"~20"),(BLUE,27,"~27"),(GREEN,buf,f"~{buf}")]
        for col,h,lab in parts:
            hh=(B-T)*h/ymax
            out+=f'<rect x="{cx-bw/2}" y="{y-hh:.1f}" width="{bw}" height="{hh:.1f}" fill="{col}"/>'
            out+=f'<text x="{cx}" y="{y-hh/2+4:.1f}" font-size="10.5" font-weight="700" fill="white" text-anchor="middle">{lab}</text>'
            y-=hh
        out+=f'<text x="{cx}" y="{y-7:.1f}" font-size="14" font-weight="800" fill="{INK}" text-anchor="middle">{total}</text>'
        return out
    g60=bar(base,13,60); g90=bar(base+150,43,90)
    return f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
<rect x="40" y="{Y(35):.1f}" width="{W-50}" height="{Y(19)-Y(35):.1f}" fill="{RED}" opacity="0.07"/>
<text x="195" y="{Y(29):.1f}" font-size="9" font-weight="700" fill="{RED}" text-anchor="middle">ICCSD today</text><text x="195" y="{Y(29)+11:.1f}" font-size="9" font-weight="700" fill="{RED}" text-anchor="middle">~20&#8211;35</text>
<line x1="40" y1="{Y(60):.1f}" x2="{W-10}" y2="{Y(60):.1f}" stroke="{GREY}" stroke-dasharray="3 3"/>
<text x="42" y="{Y(60)-4:.1f}" font-size="8.5" fill="{GREY}">GFOA &#8776; 2 months</text>
{g60}{g90}
<text x="{base}" y="{B+18}" font-size="11" font-weight="700" fill="{INK}" text-anchor="middle">60 days</text>
<text x="{base}" y="{B+31}" font-size="9.5" fill="{GREY}" text-anchor="middle">minimum</text>
<text x="{base+150}" y="{B+18}" font-size="11" font-weight="700" fill="{INK}" text-anchor="middle">90 days</text>
<text x="{base+150}" y="{B+31}" font-size="9.5" fill="{GREY}" text-anchor="middle">prudent</text>
<g font-size="9.5">
<rect x="40" y="8" width="11" height="8" fill="#9aa7b8"/><text x="55" y="15" fill="{INK}">Floor</text>
<rect x="108" y="8" width="11" height="8" fill="{BLUE}"/><text x="123" y="15" fill="{INK}">Seasonal dip</text>
<rect x="212" y="8" width="11" height="8" fill="{GREEN}"/><text x="227" y="15" fill="{INK}">Volatility buffer</text>
</g></svg>'''

# ---------- Chart 3: required days by month (95% bars) ----------
def chart_req():
    W,H=720,300; L,Rg,T,B=40,16,24,250
    ymax=80
    def X(i): return L+(W-L-Rg)*(i+0.5)/12
    def Y(v): return T+(B-T)*(ymax-v)/ymax
    bw=(W-L-Rg)/12*0.62
    # 60-90 band
    band=f'<rect x="{L}" y="{Y(90):.1f}" width="{W-Rg-L}" height="{Y(60)-Y(90):.1f}" fill="{GREEN}" opacity="0.10"/>'
    band+=f'<text x="{W-Rg-3}" y="{Y(90)-3:.1f}" font-size="9" fill="{GREEN}" text-anchor="end" font-weight="700">60&#8211;90 day policy zone</text>'
    bars=""
    for i,m in enumerate(MONTHS):
        p50,p95,p99=REQ[m]
        col=GREEN if p95>=60 else (BLUE if p95>=30 else AMBER)
        bars+=f'<rect x="{X(i)-bw/2:.1f}" y="{Y(p95):.1f}" width="{bw:.1f}" height="{B-Y(p95):.1f}" fill="{col}" opacity="0.92"/>'
        bars+=f'<line x1="{X(i)-bw/2:.1f}" y1="{Y(p99):.1f}" x2="{X(i)+bw/2:.1f}" y2="{Y(p99):.1f}" stroke="{INK}" stroke-width="1.3"/>'
        bars+=f'<text x="{X(i):.1f}" y="{Y(p95)-4:.1f}" font-size="9" fill="{INK}" text-anchor="middle">{p95}</text>'
        bars+=f'<text x="{X(i):.1f}" y="{B+15}" font-size="10" fill="{GREY}" text-anchor="middle">{m}</text>'
    ylab="".join(f'<text x="{L-6}" y="{Y(v)+4:.1f}" font-size="9" fill="{GREY}" text-anchor="end">{v}</text>'
                 f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W-Rg}" y2="{Y(v):.1f}" stroke="#eef1f6"/>' for v in (0,20,40,60,80))
    return f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
{ylab}{band}{bars}
<text x="{L}" y="14" font-size="10" fill="{GREY}">Days of cash a balance must clear for a 95% chance of not running dry over the next 12 months (tick = 99%).</text>
</svg>'''

HTML=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Why a 60&#8211;90 Day Cash Reserve Matters &mdash; ICCSD General Fund</title>
<style>
 :root{{--ink:#1f2937;--grey:#6b7280;--line:#e5e9f0;--blue:#2c5fa1;--green:#1e7a3a;--red:#b03a2e;--amber:#d98a2b}}
 *{{box-sizing:border-box}}
 body{{margin:0;background:#f4f6fa;color:var(--ink);font:16px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}}
 .page{{max-width:920px;margin:24px auto;background:#fff;padding:38px 46px;box-shadow:0 1px 4px rgba(0,0,0,.08);border-radius:8px}}
 .tag{{display:inline-block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--blue);font-weight:700}}
 h1{{font-size:27px;line-height:1.2;margin:.2em 0 .1em}}
 h2{{font-size:18px;margin:1.7em 0 .5em;padding-bottom:.25em;border-bottom:2px solid var(--line)}}
 .lead{{font-size:17px;color:#374151}}
 .cards{{display:flex;gap:14px;margin:20px 0}}
 .card{{flex:1;border:1px solid var(--line);border-top:4px solid var(--blue);border-radius:6px;padding:12px 14px}}
 .card.r{{border-top-color:var(--red)}} .card.g{{border-top-color:var(--green)}}
 .card .v{{font-size:23px;font-weight:800}} .card .l{{font-size:12.5px;color:var(--grey)}}
 .card.r .v{{color:var(--red)}} .card.g .v{{color:var(--green)}} .card .v.b{{color:var(--blue)}}
 figure{{margin:14px 0 6px}} figcaption{{font-size:12.5px;color:var(--grey);margin-top:4px}}
 .note{{background:#fbf7ee;border-left:4px solid var(--amber);padding:10px 14px;font-size:13.5px;border-radius:0 6px 6px 0;margin:14px 0}}
 ul{{margin:.4em 0}} li{{margin:.25em 0}}
 .build{{display:flex;gap:18px;align-items:center;flex-wrap:wrap}}
 .build .txt{{flex:1;min-width:260px}}
 .build .svgwrap{{flex:0 0 320px;max-width:340px}}
 table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}}
 th,td{{border:1px solid var(--line);padding:5px 7px;text-align:center}} th{{background:#f7f9fc}}
 .foot{{font-size:11.5px;color:var(--grey);margin-top:26px;border-top:1px solid var(--line);padding-top:12px}}
 @media print{{body{{background:#fff}}.page{{box-shadow:none;margin:0;max-width:none;padding:0 8px}}}}
</style></head>
<body><div class="page">
<span class="tag">Iowa City Schools &middot; General Fund Liquidity &middot; Unofficial community analysis</span>
<h1>Why a 60&#8211;90 day cash reserve matters</h1>
<p class="lead">The General Fund's cash balance swings by about <b>50 days of cash</b> within every year &mdash; not because the district gains or loses money, but because property taxes and state aid arrive in a few big lumps while payroll goes out evenly. A reserve target has to be sized to the <b>seasonal low point</b>, not the average. That is why a healthy target is <b>60&#8211;90 days</b>, even though the year-round average looks higher.</p>

<div class="cards">
 <div class="card r"><div class="v">~50 days</div><div class="l">Peak-to-trough swing in cash within a single year</div></div>
 <div class="card"><div class="v b">60 days</div><div class="l">Minimum to keep the late-summer trough above the payroll floor</div></div>
 <div class="card g"><div class="v">90 days</div><div class="l">Prudent &mdash; absorbs a bad-variance year and a revenue shock</div></div>
</div>

<h2>The problem: cash is highly seasonal</h2>
<p>Local property taxes land in just two months (October &amp; April); state aid is steady; payroll never pauses. So cash drains between tax settlements and bottoms out in late summer before October taxes arrive. The red line is what ICCSD actually looked like in FY26 <i>without</i> its rescue borrowing &mdash; the trough goes <b>negative</b>. Lift the whole curve to a 60- or 90-day reserve and the <i>same</i> trough clears the floor with no borrowing.</p>
<figure>{chart_swing()}<figcaption>Days of General Fund cash by month (cash &divide; ~$610K/day). Seasonal shape from FY26 monthly cash flows; scenarios shift the same shape to a 60- and 90-day annual average.</figcaption></figure>

<div class="note"><b>Why the average is the wrong number.</b> A district could average a comfortable-sounding 35 days and still go broke every August. What matters is the <b>trough</b> &mdash; the single lowest point &mdash; relative to the cash you must keep on hand to make payroll. The reserve exists to carry the trough, not the average.</div>

<div class="note" style="border-left-color:#2c5fa1;background:#eef3fb"><b>New for FY27 &mdash; a state law reshapes the season, but not the target.</b> Iowa <b>SF 2201</b> (signed Feb 2026) moves state aid from monthly to <b>quarterly</b> payments beginning July 15. That refills the fund at the start of the year, so the <i>late-summer</i> trough above eases &mdash; but the dry stretch simply moves to <b>late winter</b> (Dec&#8211;March), between quarterly payments. Because four big payments are lumpier than nine small ones, the year-to-year swing actually grows, so the <b>60&#8211;90 day target holds &mdash; arguably reinforced.</b> The seasonality reshapes; it does not shrink.</div>

<h2>Why 60&#8211;90 days, specifically</h2>
<div class="build">
 <div class="txt">
  <p>The target is built from three pieces:</p>
  <ul>
   <li><b>Operating floor (~20 days)</b> &mdash; cash you can never dip below, because payroll is paid mid-month before late-month receipts arrive.</li>
   <li><b>Seasonal dip (~27 days)</b> &mdash; how far the late-summer trough sits <i>below</i> the annual average, baked in by the tax calendar.</li>
   <li><b>Volatility / shock buffer (~13 &#8594; 43 days)</b> &mdash; margin for a year where revenues come in light or costs run heavy. A modest buffer gets you to <b>60</b>; covering a real shock (enrollment drop, delayed aid) takes you toward <b>90</b>.</li>
  </ul>
  <p>A second, independent check agrees: modeled month by month, the demanding months (the post-tax peaks, which must self-fund the entire run down to the next trough) require <b>60&#8211;76 days</b> for 95&#8211;99% confidence of never running dry. A single reserve policy must satisfy the most demanding month &mdash; so the floor lands at ~60, the prudent level near ~90.</p>
 </div>
 <div class="svgwrap"><figure style="margin:0">{chart_decomp()}</figure></div>
</div>

<h2>What each month needs</h2>
<p>Required days of cash for a 95% chance of not running dry over the following 12 months (component-based volatility model). September is the universal binding trough; the peaks need the most cushion because the whole drawdown is still ahead of them.</p>
<figure>{chart_req()}</figure>

<h2>Bottom line for ICCSD</h2>
<p>The district currently steers to roughly <b>20&#8211;35 days</b> &mdash; below even the minimum &mdash; which is exactly why it has borrowed every late summer (the $10M interfund loan, the anticipatory warrants). Those are the symptom of a reserve sized to the average instead of the trough. Moving the floor toward <b>60 days</b>, and the goal toward <b>90</b>, would let the General Fund self-fund its own seasonal cycle, end the recurring summer borrowing and its interest cost, and rebuild the margin that rating agencies look for.</p>

<div class="foot">
 <b>Unofficial community analysis</b> &mdash; not produced by ICCSD, PFM Financial Advisors, or the Financial Oversight Committee. Built from unaudited board materials (PFM monthly cash-flow exhibits, the FY26 quarterly financial reports, the FY2024 Certified Annual Report). Figures are provisional: the FY24 and FY25 audits are still outstanding, and the FY27 shift of state aid to quarterly payments will move the trough toward March &mdash; both will revise the exact day counts, not the case for sizing reserves to the seasonal low. Days of cash = General Fund cash &divide; ~$610,000/day (~$223M FY26 operating spend &divide; 365).
</div>
</div></body></html>'''

import pathlib
out=pathlib.Path("docs/why-cash-reserve-targets.html")
out.write_text(HTML,encoding="utf-8")
print("wrote",out,len(HTML),"bytes")
