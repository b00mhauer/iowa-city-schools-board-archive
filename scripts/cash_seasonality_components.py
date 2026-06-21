"""Component-based refinement of the GF liquidity model.

Improvement over the flat-sigma version: instead of one assumed monthly
flow volatility, sigma is built from the volatility of each flow COMPONENT,
which lets the ~85% of the flow that is statutory/contractual contribute
almost no forecast error and concentrates uncertainty where it actually
lives (the lumpy 'other local/federal' residual + property-tax timing).

Component volatilities (std dev of monthly forecast error, $M), estimated
from FY25 vs FY26 monthly category data (Q3 FY26 report) and the statutory
calendar:
    state foundation aid .... 0.15   (fixed formula / schedule)
    payroll & benefits ...... 0.50   (set by contracts)
    property-tax AMOUNT ...... ~0     (statutory levy)
    property-tax TIMING ...... 2.50   (only on the two settlement months)
    other local/fed/misc .... 1.50   (the genuine residual; dominates)
=> sigma ~ $1.6M ordinary months, ~$3.0M on the Oct & Apr settlement months.
"""
from __future__ import annotations
import numpy as np

MONTHS = ["Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun"]
MU = np.array([-9_928_258,-13_416_091,-895_687,28_899_706,-2_256_184,-5_379_096,
               -6_778_899,-3_409_798,-1_960_135,22_856_394,-670_255,-6_467_753],float)
DAY = 610_000.0

s_aid, s_pay, s_other, s_taxtiming = 0.15e6, 0.50e6, 1.50e6, 2.50e6
base = np.sqrt(s_aid**2 + s_pay**2 + s_other**2)         # ordinary month
taxm = np.sqrt(base**2 + s_taxtiming**2)                 # Oct & Apr
SIGMA = np.array([base,base,base,taxm,base,base,base,base,base,taxm,base,base])
print("component sigma by month ($M):", np.round(SIGMA/1e6,2).tolist())

def required(sigma_vec, N=400_000, seed=1):
    rng = np.random.default_rng(seed); out={}
    for start in range(12):
        idx=[(start+1+k)%12 for k in range(12)]
        m=MU[idx]; sig=sigma_vec[idx]
        cum=np.cumsum(m[None,:]+rng.normal(0,1,(N,12))*sig[None,:],axis=1)
        rmin=cum.min(axis=1)
        out[MONTHS[start]]={p:max(-np.percentile(rmin,(1-z)*100),0)/DAY
                            for p,z in [("50%",.5),("95%",.95),("99%",.99),("99.9%",.999)]}
    return out

r=required(SIGMA)
print(f"\nRefined required days (component sigma):")
print(f"{'End of':>6} | {'50%':>5} | {'95%':>5} | {'99%':>5} | {'99.9%':>6}")
for mo in MONTHS:
    x=r[mo]; print(f"{mo:>6} | {x['50%']:5.0f} | {x['95%']:5.0f} | {x['99%']:5.0f} | {x['99.9%']:6.0f}")
