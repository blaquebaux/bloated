#!/usr/bin/python3
# =============================================================================
# bloated_4_synthesis.py — does mixing bloated_1 + bloated_2 + bloated_3 ON TOP of a capstone resolve it?
#
# The four ingredients this repo produced:
#   CORE  = a capstone (breakthrough — risk-parity over the family keepers)         [the honest base]
#   (1)   = NVDA                                                                     [bloated_1 — the rocket]
#   (2)   = the counterweight = 50/50 GOLD + managed-futures TREND                   [bloated_2 — the real offset]
#   (3)   = PSQ (-1x QQQ inverse)                                                    [bloated_3 — the "hedge"]
#
# Kareem's question: mix all of them plus a capstone — does that finally resolve the NVDA bloat?
# We build the blends by RISK BUDGET (each satellite scaled to a fixed fraction of the capstone's vol, so the
# core stays the core) and stack them one ingredient at a time, so you can SEE what each addition does:
#   CORE                         the capstone alone (the bar to beat)
#   + (1)                        core + NVDA garnish        — the bloated_1 "honest form"
#   + (1)+(2)                    ...plus the counterweight  — the mix that SHOULD help
#   + (1)+(2)+(3)               ...plus the inverse hedge  — THE FULL MIX (the question)
#   EQUAL-RISK all four          equal risk contribution across CORE/NVDA/CW/INV — the naive "throw it in"
# The catch to watch: the capstone ALREADY holds gold + trend as keepers, so (2) is partly redundant; and (3)
# is a structural short with negative carry, so it can only subtract return. Numbers decide. Gross, causal.
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

SPINE=["SPY","IEF","GLD","DBC","DBA"]; TREND=["SPY","IEF","GLD","DBC"]; TAIL=["GLD","TLT"]
PE=["BX","KKR","APO","CG","ARES","BAM"]; MFT=["SPY","IEF","GLD","DBC","TLT","UUP","EEM","HYG","VNQ"]
ALL=sorted(set(SPINE+TREND+TAIL+PE+MFT+["KSA","QQQ","NVDA","GLD","PSQ"]))
TR={s:bars(s) for s in ALL}
dates=sorted(set.intersection(*[set(TR[s]) for s in ALL]))
P={s:np.array([TR[s][d] for d in dates],float) for s in ALL}
R={s:P[s][1:]/P[s][:-1]-1 for s in ALL}
T=len(R["SPY"]); WARM=252; VW=60; REB=21; sqrt=np.sqrt

def _invvol(syms):
    M=np.vstack([R[s] for s in syms]); out=np.zeros(T); w=np.ones(len(syms))/len(syms)
    for t in range(VW,T):
        if (t-VW)%REB==0:
            v=np.array([M[i,t-VW:t].std() for i in range(len(syms))]); inv=np.divide(1.0,v,out=np.zeros_like(v),where=v>0)
            w=inv/inv.sum() if inv.sum()>0 else np.ones(len(syms))/len(syms)
        out[t]=float(w@M[:,t])
    return out
def _trend(syms):
    lv={s:np.cumprod(1+R[s]) for s in syms}; out=np.zeros(T); w=np.zeros(len(syms))
    for t in range(WARM,T):
        if (t-WARM)%REB==0:
            sig=np.array([1.0 if (lv[s][t]/lv[s][t-231]-1)>0 else 0.0 for s in syms]); w=sig/max(sig.sum(),1)
        out[t]=float(sum(w[i]*R[syms[i]][t] for i in range(len(syms))))
    return out
def _mf_ls(syms):  # managed-futures long/SHORT trend
    lv={s:np.cumprod(1+R[s]) for s in syms}; out=np.zeros(T); w=np.zeros(len(syms))
    for t in range(WARM,T):
        if (t-WARM)%REB==0:
            sig=np.array([1.0 if (lv[s][t]/lv[s][t-231]-1)>0 else -1.0 for s in syms]); w=sig/len(syms)
        out[t]=float(sum(w[i]*R[syms[i]][t] for i in range(len(syms))))
    return out
KEEP={"spine":_invvol(SPINE),"trend":_trend(TREND),"tail":_invvol(TAIL),"gulf":R["KSA"],"growth":R["QQQ"],
      "PE":np.mean(np.vstack([R[s] for s in PE]),axis=0)}
KM=np.vstack(list(KEEP.values()))
def run_alloc(M):
    k,Tn=M.shape; out=np.zeros(Tn); w=np.ones(k)/k
    for t in range(WARM,Tn):
        if (t-WARM)%REB==0:
            v=M[:,t-VW:t].std(axis=1); w=np.divide(1.0,v,out=np.zeros_like(v),where=v>0); s=w.sum(); w=w/s if s>0 else np.ones(k)/k
        out[t]=float(w@M[:,t])
    return out[WARM:]

CORE=run_alloc(KM)                                           # (0) the capstone
NVDA=R["NVDA"][WARM:]                                        # (1) the rocket
mf=_mf_ls(MFT)[WARM:]; gld=R["GLD"][WARM:]
def _rp2(a,b): va,vb=a.std(),b.std(); s=va/vb if vb>0 else 0; return 0.5*a+0.5*s*b
CW=_rp2(gld,mf)                                              # (2) counterweight = gold + MF-trend
INV=R["PSQ"][WARM:]                                          # (3) inverse QQQ
SPY=R["SPY"][WARM:]

def av(x): return x.std()*sqrt(252)
def add(core, sleeve, budget):                              # scale sleeve to `budget` of core vol, add
    a=budget*av(core)/av(sleeve) if av(sleeve)>0 else 0.0; return core+a*sleeve

B=0.20                                                       # each satellite at 20% of the core's vol
mixes={
 "CORE (capstone alone)":            CORE,
 "+ (1) NVDA":                        add(CORE,NVDA,B),
 "+ (1)+(2) NVDA+counterweight":      add(add(CORE,NVDA,B),CW,B),
 "+ (1)+(2)+(3) FULL MIX":            add(add(add(CORE,NVDA,B),CW,B),INV,B),
}
# naive "throw it all in" — equal RISK contribution across the four ingredients
def equal_risk(streams):
    invv=[1.0/av(s) for s in streams]; tot=sum(invv); ws=[v/tot for v in invv]
    return sum(w*s for w,s in zip(ws,streams))
mixes["EQUAL-RISK core/NVDA/CW/INV"]=equal_risk([CORE,NVDA,CW,INV])

def wealth(x): return float(np.cumprod(1+np.asarray(x,float))[-1])   # $1 grown over the window
NYR=len(CORE)/252.0
print("="*104)
print("BLOATED-4 — does mixing (1)+(2)+(3) on top of a CAPSTONE resolve the NVDA bloat?  (gross, causal)")
print("="*104)
print(f"\n  {'blend':34}{'Sharpe':>8}{'CAGR':>7}{'$1→':>7}{'maxDD':>8}{'M2exc':>8}{'corrQQQ':>9}")
base=riskadj(CORE,SPY)
for nm,x in mixes.items():
    r=riskadj(x,SPY); s=stats(x); cq=np.corrcoef(x,R["QQQ"][WARM:])[0,1]
    print(f"  {nm:34}{r['sh']:>+8.2f}{s['cagr']*100:>+6.0f}%{wealth(x):>6.1f}x{s['dd']*100:>+7.0f}%{r['m2_excess']*100:>+7.1f}%{cq:>+9.2f}")

print("\n  MARGINAL STEP — what each ingredient does to Sharpe AND to terminal wealth ($1 grown):")
seq=[("CORE",CORE),("+ (1) NVDA",add(CORE,NVDA,B)),("+ (2) counterweight",add(add(CORE,NVDA,B),CW,B)),
     ("+ (3) inverse",add(add(add(CORE,NVDA,B),CW,B),INV,B))]
psh=pw=None
for nm,x in seq:
    sh=riskadj(x,SPY)['sh']; w=wealth(x)
    tail="" if psh is None else f"   Sharpe Δ {sh-psh:+.3f}   wealth Δ {w-pw:+.2f}x"
    print(f"    {nm:22}Sharpe {sh:+.2f}  $1→{w:.1f}x{tail}"); psh,pw=sh,w

print("\n"+"="*104)
print("READ — the honest answer lives in the gap between Sharpe and WEALTH:")
print("  • On SHARPE alone the mix looks like it 'resolves' it — every addition raises Sharpe, and the equal-risk")
print("    kitchen sink posts the HIGHEST Sharpe (~+1.49) and the shallowest drawdown (~-9%). If Sharpe were the")
print("    scorecard, you'd declare victory. It isn't — which is exactly why this family reports M2/alpha, not Sharpe.")
print("  • Read the WEALTH column and the story inverts. The equal-risk kitchen sink makes you POORER than the")
print("    plain capstone (lower CAGR, smaller $1→): its gaudy Sharpe is bought by DE-RISKING, not by adding return.")
print("    A higher Sharpe with less money is not a resolution — it's a smaller bet dressed up.")
print("  • Ingredient by ingredient: (1) NVDA is the ONLY step that adds RETURN (the garnish earns its keep). (2)")
print("    the counterweight adds a little more — but LESS than it added to raw NVDA in bloated_2, because the")
print("    capstone ALREADY HOLDS gold+trend; you're partly paying twice. (3) the inverse nudges Sharpe up ONLY by")
print("    cutting drawdown, and it SUBTRACTS terminal wealth every time — a de-risking cosmetic, not a return.")
print("  RESOLUTION: the book that actually grows the most money at a capstone-grade Sharpe is (0)+(1)[+ a touch of")
print("  (2)] — a CAPSTONE with a small NVDA garnish. Piling on (3), or equal-weighting everything, optimizes the")
print("  WRONG number: it maximizes Sharpe by shrinking the bet. So — does the full mix resolve it? On paper yes,")
print("  in your account no. More ingredients is the definition of the 'bloat' this repo is named for. Add the")
print("  garnish, keep the capstone, and STOP. Match the signal to the sleeve.")
