"""Forward-looking refresh under SF 2201 (signed Feb 2026).

Key change: state foundation aid moves from MONTHLY (≈$10.6M, Sept-June) to
QUARTERLY (≈$26.5M) beginning July 15. This refills the General Fund at the
start of the fiscal year and removes the late-summer gap that has been the
binding constraint in the FY26-based model.

We re-estimate required days-of-cash using the FY27 operating flow vector
(reconstructed from PFM Exhibit 2a, which already assumes quarterly aid),
and compare to the FY26 (pre-law) baseline. Component-based sigma as before.
PFM placed the quarterly payments in Aug/Nov/Feb/May; the statute says
'beginning July 15', which would put them one month earlier (Jul/Oct/Jan/Apr)
and improve summer liquidity even more -- flagged, not yet modeled.
"""
from __future__ import annotations
import numpy as np
M=["Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun"]
DAY=610_000.0

# FY26 pre-law operating flows (monthly aid) -- the baseline used so far
MU26=np.array([-9_928_258,-13_416_091,-895_687,28_899_706,-2_256_184,-5_379_096,
               -6_778_899,-3_409_798,-1_960_135,22_856_394,-670_255,-6_467_753],float)
# FY27 post-law operating flows (quarterly aid Aug/Nov/Feb/May), from PFM Exhibit 2a
MU27=np.array([-10_944_939,13_380_971,-11_286_982,22_507_526,13_891_807,-15_770_834,
               -17_935_180,9_899_389,-13_635_520,16_773_681,12_033_035,-16_804_192],float)

base=np.sqrt(0.15e6**2+0.50e6**2+1.50e6**2)
taxm=np.sqrt(base**2+2.50e6**2)
SIG=np.array([base,base,base,taxm,base,base,base,base,base,taxm,base,base])

def req(mu,N=400_000,seed=1):
    rng=np.random.default_rng(seed); out={}
    for s in range(12):
        idx=[(s+1+k)%12 for k in range(12)]
        cum=np.cumsum(mu[idx][None,:]+rng.normal(0,1,(N,12))*SIG[idx][None,:],axis=1)
        rmin=cum.min(axis=1)
        out[M[s]]={p:max(-np.percentile(rmin,(1-z)*100),0)/DAY
                   for p,z in[("50",.5),("95",.95),("99",.99)]}
    return out

r26,r27=req(MU26),req(MU27)
print("Required days of cash -- PRE-law (FY26 monthly aid)  vs  POST-law (FY27 quarterly aid)")
print(f"{'End of':>6} | {'50% old':>7} {'95% old':>7} {'99% old':>7} || {'50% NEW':>7} {'95% NEW':>7} {'99% NEW':>7} | {'d95':>5}")
for mo in M:
    a,b=r26[mo],r27[mo]
    print(f"{mo:>6} | {a['50']:7.0f} {a['95']:7.0f} {a['99']:7.0f} || {b['50']:7.0f} {b['95']:7.0f} {b['99']:7.0f} | {b['95']-a['95']:+5.0f}")

# annual worst month (the single reserve target driver)
w26=max(r26[m]['95'] for m in M); w27=max(r27[m]['95'] for m in M)
print(f"\nWorst-month 95% requirement (drives a single reserve target): pre-law {w26:.0f}d  ->  post-law {w27:.0f}d")
