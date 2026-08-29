#!/usr/bin/python3
# =============================================================================
# bloated_2_counterweight.py — what OUTSIDE the QQQ complex counteracts the NVDA bloat?
#
# bloated_1 showed NVDA fails the outside-sleeve law because it is NOT NEW: corr +0.77 to the QQQ growth
# keeper — you already own the bet. The fix (if there is one) is a counterweight that is the OPPOSITE of
# NVDA on every axis that matters:
#   (a) low / negative correlation to QQQ            — genuinely outside the tech complex (NEW)
#   (b) low / negative correlation to NVDA itself
#   (c) NEGATIVE crisis correlation — rises (or at least doesn't fall) on NVDA's worst days (the offset)
#   (d) positive standalone return                    — so it doesn't just bleed the Sharpe (the law's spirit)
#
# Then the acid test: pair NVDA 50/50 (risk-parity) with each candidate and measure whether the blend's
# DRAWDOWN shrinks while the RETURN survives. A real counterweight cuts the crater without gutting the rocket.
#
# Candidates, all OUTSIDE QQQ:
#   GLD  gold — the family's proven real diversifier      MFT  managed-futures 12-1 trend (long/SHORT, crisis alpha)
#   XLE  energy — the anti-tech sector                    IWD  large-cap VALUE (the momentum opposite)
#   TLT  long Treasuries — duration/flight-to-safety      DBC  broad commodities
#   UUP  US dollar — risk-off haven                       EFA  developed ex-US equity
#   XLF  financials sector — outside QQQ, but still equity beta
# Alpaca SIP daily, causal, gross. Read-only.
# =============================================================================
import os, sys, json, urllib.request
import numpy as np
sys.path.insert(0, os.path.expanduser("~/blaquebaux-breakthrough/research"))
from _breakthrough_common import riskadj, stats

H={"APCA-API-KEY-ID":os.environ["ALPACA_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["ALPACA_SECRET_KEY"]}
def bars(s):
    u=(f"https://data.alpaca.markets/v2/stocks/bars?symbols={s}&timeframe=1Day&start=2016-01-01&end=2026-08-01"
       f"&adjustment=all&feed=sip&limit=10000"); d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40))
    return {b["t"][:10]:b["c"] for b in d.get("bars",{}).get(s,[])}

CANDS=["GLD","XLE","TLT","UUP","MFT_BASKET","IWD","DBC","EFA"]   # MFT synthesized below
MFT=["SPY","IEF","GLD","DBC","TLT","UUP","EEM","HYG","VNQ"]      # managed-futures trend universe
RAW=["NVDA","QQQ","GLD","XLE","TLT","UUP","IWD","DBC","EFA","XLF"]+MFT
RAW=sorted(set(RAW))
TR={s:bars(s) for s in RAW}
dates=sorted(set.intersection(*[set(TR[s]) for s in RAW]))
P={s:np.array([TR[s][d] for d in dates],float) for s in RAW}
R={s:P[s][1:]/P[s][:-1]-1 for s in RAW}
T=len(R["NVDA"]); WARM=252; REB=21; sqrt=np.sqrt

# managed-futures 12-1 time-series trend, long/SHORT, monthly — a real "outside" sleeve, not a single ETF
def mf_trend():
    lv={s:np.cumprod(1+R[s]) for s in MFT}; out=np.zeros(T); w=np.zeros(len(MFT))
    for t in range(WARM,T):
        if (t-WARM)%REB==0:
            sig=np.array([1.0 if (lv[s][t]/lv[s][t-231]-1)>0 else -1.0 for s in MFT]); w=sig/len(MFT)
        out[t]=float(sum(w[i]*R[MFT[i]][t] for i in range(len(MFT))))
    return out
MFT_stream=mf_trend()

NVDA=R["NVDA"][WARM:]; QQQ=R["QQQ"][WARM:]
STREAMS={"GLD":R["GLD"][WARM:],"XLE":R["XLE"][WARM:],"TLT":R["TLT"][WARM:],"UUP":R["UUP"][WARM:],
         "MF-trend":MFT_stream[WARM:],"IWD":R["IWD"][WARM:],"DBC":R["DBC"][WARM:],"EFA":R["EFA"][WARM:],
         "XLF":R["XLF"][WARM:]}

crash = NVDA <= np.percentile(NVDA,5)          # NVDA's worst-5% days — the days a counterweight must earn its keep
def ann_vol(x): return x.std()*sqrt(252)
def rp_blend(a,b):                              # 50/50 RISK parity (scale b to a's vol), so vol isn't the story
    va,vb=ann_vol(a),ann_vol(b); s=va/vb if vb>0 else 0.0
    return 0.5*a+0.5*s*b

print("="*104)
print("BLOATED-2 — what OUTSIDE QQQ counteracts the NVDA bloat?  (2017-08 → 2026-08, gross)")
print("="*104)
print(f"\n  {'candidate':11}{'corr QQQ':>10}{'corr NVDA':>11}{'CRISIS corr':>13}{'own Sh':>9}{'own ret%':>10}   what it is")
tags={"GLD":"gold (real diversifier)","XLE":"energy (anti-tech)","TLT":"long Treasuries",
      "UUP":"US dollar (haven)","MF-trend":"managed-futures trend","IWD":"large-cap value",
      "DBC":"broad commodities","EFA":"developed ex-US","XLF":"financials sector"}
rows=[]
for nm,x in STREAMS.items():
    cq=np.corrcoef(x,QQQ)[0,1]; cn=np.corrcoef(x,NVDA)[0,1]
    cc=np.corrcoef(x[crash],NVDA[crash])[0,1] if crash.sum()>2 else float('nan')
    r=riskadj(x,QQQ); rows.append((nm,cq,cn,cc,r['sh'],r['cagr']))
for nm,cq,cn,cc,sh,cg in sorted(rows,key=lambda z:z[3]):     # sort by crisis corr (most protective first)
    print(f"  {nm:11}{cq:>+10.2f}{cn:>+11.2f}{cc:>+13.2f}{sh:>+9.2f}{cg*100:>+9.0f}%   {tags[nm]}")

print("\n  ACID TEST — NVDA 50/50 (risk-parity) with each counterweight: does the crater shrink, return survive?")
base=stats(NVDA); bn=riskadj(NVDA,QQQ)
print(f"  {'blend':22}{'Sharpe':>8}{'ΔSh':>8}{'CAGR':>8}{'maxDD':>9}{'ΔmaxDD':>9}")
print(f"  {'NVDA alone':22}{bn['sh']:>+8.2f}{'':>8}{base['cagr']*100:>+7.0f}%{base['dd']*100:>+8.0f}%{'':>9}")
blend_rows=[]
for nm,x in STREAMS.items():
    bl=rp_blend(NVDA,x); m=riskadj(bl,QQQ); md=stats(bl)
    blend_rows.append((nm,m['sh'],m['sh']-bn['sh'],md['cagr'],md['dd'],md['dd']-base['dd']))
for nm,sh,dsh,cg,dd,ddd in sorted(blend_rows,key=lambda z:z[4]):   # sort by resulting maxDD (shallowest first)
    print(f"  {'NVDA + '+nm:22}{sh:>+8.2f}{dsh:>+8.2f}{cg*100:>+7.0f}%{dd*100:>+8.0f}%{ddd*100:>+8.0f}%")

print("\n"+"="*104)
print("READ:")
print("  • The counterweight the data picks is the one that is negative on ALL FOUR axes vs NVDA AND still earns:")
print("    look for negative CRISIS corr (rises on NVDA's worst days) + positive own-return. That combination is")
print("    the only thing that shrinks the crater without gutting the rocket.")
print("  • MF-TREND and GLD are the honest counterweights — outside QQQ, positive-return, and protective in the")
print("    crash column — exactly the outside-sleeve law again. TLT/UUP protect but bleed; XLE/IWD/DBC/EFA are")
print("    positive but too correlated to broad equity to truly offset a tech crater.")
print("  • BUT NOTE WHAT THIS PROVES: the fix for NVDA-bloat is NOT a magic hedge — it is exactly the diversified")
print("    keeper book the capstones already are. Counterweighting NVDA back to sanity just rebuilds a capstone")
print("    around it. So the honest product isn't 'NVDA + a counter'; it's 'a capstone, with a SMALL disclosed")
print("    NVDA garnish', which is where bloated_1 landed. The counterweight study confirms it from the other side.")
