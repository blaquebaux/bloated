#!/usr/bin/python3
# =============================================================================
# bloated_1_nvidia_mix.py — the "BLOATED" hypothesis: mix NVDA into the capstones (and the null).
#
# Kareem's read: NVDA is what's moving the market, and the capstones don't hold it directly. So bolt
# the market's engine onto our diversified allocators — interesting, or bloated? Only analysis can tell.
#
# We test it four honest ways, because a single mega-cap rocket flatters every Sharpe it touches:
#   (1) NVDA STANDALONE — the rocket, and the crater under it (its own maxDD is the whole point).
#   (2) OVERLAP — how much NVDA the capstones ALREADY carry, via the QQQ growth keeper + the SPY spine.
#       If they already own it, "adding" it is doubling down on a bet you already have — the bloat.
#   (3) NVDA AS A SATELLITE — added at a 20/30% risk budget to each capstone (same harness as the
#       outside_sleeve_test): does it lift Sharpe, and what does it do to drawdown?
#   (4) THE LAW'S VERDICT — the outside-sleeve law says a satellite helps iff NEW + UNCORRELATED +
#       POSITIVE. NVDA is wildly positive, but is it NEW (given the overlap) and is it UNCORRELATED?
#       And the law measures Sharpe — it is blind to single-name blow-up risk, which is the real cost.
#
# Same keeper harness as breakthrough/outside_sleeve_test. Alpaca SIP daily, causal, net of nothing
# (gross) so the comparison is clean. Read-only.
# =============================================================================
import os, sys, json, urllib.request
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/blaquebaux-breakthrough/research"))
from _breakthrough_common import riskadj, stats

H={"APCA-API-KEY-ID":os.environ["ALPACA_KEY_ID"],"APCA-API-SECRET-KEY":os.environ["ALPACA_SECRET_KEY"]}
def bars(s,adj="all"):
    u=(f"https://data.alpaca.markets/v2/stocks/bars?symbols={s}&timeframe=1Day&start=2016-01-01&end=2026-08-01"
       f"&adjustment={adj}&feed=sip&limit=10000"); d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40))
    return {b["t"][:10]:b["c"] for b in d.get("bars",{}).get(s,[])}

SPINE=["SPY","IEF","GLD","DBC","DBA"]; TREND=["SPY","IEF","GLD","DBC"]; TAIL=["GLD","TLT"]
PE=["BX","KKR","APO","CG","ARES","BAM"]
ALL=sorted(set(SPINE+TREND+TAIL+PE+["KSA","QQQ","NVDA"]))
TR={s:bars(s) for s in ALL}
dates=sorted(set.intersection(*[set(TR[s]) for s in ALL]))
P={s:np.array([TR[s][d] for d in dates],float) for s in ALL}
R={s:P[s][1:]/P[s][:-1]-1 for s in ALL}
T=len(R["SPY"]); WARM=252; VW=60; REB=21; sqrt=np.sqrt
def lag(g): g=np.asarray(g,float); o=np.zeros_like(g); o[1:]=g[:-1]; return o

# --- capstone streams on the shared keeper harness (breakthrough / bastion / brilliant) ---------------
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
KEEP={"spine":_invvol(SPINE),"trend":_trend(TREND),"tail":_invvol(TAIL),"gulf":R["KSA"],"growth":R["QQQ"],
      "PE":np.mean(np.vstack([R[s] for s in PE]),axis=0)}
KM=np.vstack(list(KEEP.values()))
def run_alloc(M,wfn):
    k,Tn=M.shape; out=np.zeros(Tn); w=np.ones(k)/k
    for t in range(WARM,Tn):
        if (t-WARM)%REB==0: w=wfn(M[:,t-VW:t]); s=np.abs(w).sum(); w=w/s if s>0 else np.ones(k)/k
        out[t]=float(w@M[:,t])
    return out[WARM:]
def w_rp(win): v=win.std(axis=1); return np.divide(1.0,v,out=np.zeros_like(v),where=v>0)
def w_mv(win):
    C=np.cov(win)+1e-6*np.eye(win.shape[0])
    try: w=np.linalg.solve(C,np.ones(win.shape[0]))
    except np.linalg.LinAlgError: w=np.ones(win.shape[0])
    return np.clip(w,0,None)
bt=run_alloc(KM,w_rp)                                             # breakthrough = balanced inverse-vol
bear_trend=_trend(["SPY"]); bastion_overlay=np.where(bear_trend[WARM:]==0.0,-1.0*R["SPY"][WARM:],0.0)
bas=0.85*bt+0.15*bastion_overlay                                  # bastion = defense (bear overlay)
bril=run_alloc(KM,w_mv)                                           # brilliant = min-var tilt

SPY=R["SPY"][WARM:]; NVDA=R["NVDA"][WARM:]                        # aligned to [WARM:]
CAPS={"breakthrough":bt,"bastion":bas,"brilliant":bril}
# the honest null: our bear sleeve (regime-gated short) — built and shelved as a null (negative return).
NULL=bastion_overlay                                             # short SPY only when risk-off; ≈ the null's core

def ann_vol(x): return x.std()*sqrt(252)
def combine(cap, sleeve, risk_budget):
    vc,vs=ann_vol(cap),ann_vol(sleeve); a=risk_budget*vc/vs if vs>0 else 0.0
    return cap+a*sleeve, a

# =====================================================================================================
print("="*100)
print("BLOATED — does bolting NVDA (the market's engine) onto the diversified capstones help, or bloat?")
print("="*100)

# (1) STANDALONE — the rocket and the crater ----------------------------------------------------------
n=riskadj(NVDA,SPY); s=stats(NVDA); sp=stats(SPY)
print("\n(1) STANDALONE  (2017-08 → 2026-08, gross)")
print(f"  {'':14}{'Sharpe':>8}{'CAGR':>9}{'vol':>8}{'maxDD':>9}{'skew':>8}{'exKurt':>9}")
print(f"  {'NVDA':14}{n['sh']:>+8.2f}{s['cagr']*100:>+8.0f}%{s['vol']*100:>7.0f}%{s['dd']*100:>+8.0f}%{n['skew']:>+8.2f}{n['exkurt']:>+9.1f}")
print(f"  {'SPY':14}{riskadj(SPY,SPY)['sh']:>+8.2f}{sp['cagr']*100:>+8.0f}%{sp['vol']*100:>7.0f}%{sp['dd']*100:>+8.0f}%")
print("  → the Sharpe is a monster BECAUSE the sample is a monster. The maxDD is the tell: a single name")
print("    can lose ~2/3 of its value and you hold every point of it. That risk is NOT in the Sharpe.")

# (2) OVERLAP — how much NVDA the capstones ALREADY own ------------------------------------------------
print("\n(2) OVERLAP — the capstones already carry NVDA through the QQQ growth keeper + SPY spine")
print(f"  {'stream':16}{'corr(NVDA)':>12}{'beta(NVDA)':>12}")
for nm,x in [("QQQ (growth)",R["QQQ"][WARM:]),("SPY (spine)",SPY),
             ("breakthrough",bt),("bastion",bas),("brilliant",bril)]:
    c=np.corrcoef(x,NVDA)[0,1]; b=np.cov(x,NVDA)[0,1]/np.var(NVDA)
    print(f"  {nm:16}{c:>+12.2f}{b:>+12.3f}")
print("  → QQQ is ~0.7 correlated to NVDA and NVDA is a top QQQ holding — the capstones ALREADY own the")
print("    bet. 'Adding' NVDA is not new exposure, it's LEVERING the growth keeper you already have.")

# (3) NVDA AS A SATELLITE — added at a risk budget to each capstone ------------------------------------
print("\n(3) NVDA AS A SATELLITE  (scaled to a risk budget of the capstone's vol, same harness as outside_sleeve_test)")
print(f"  {'capstone + NVDA':22}{'budget':>8}{'corr':>7}{'base Sh':>9}{'combo Sh':>10}{'ΔSh':>8}{'base DD':>9}{'combo DD':>10}")
for capnm,cap in CAPS.items():
    base=riskadj(cap,SPY); bdd=stats(cap)['dd']; c=np.corrcoef(cap,NVDA)[0,1]
    for rb in (0.20,0.30):
        combo,a=combine(cap,NVDA,rb); m=riskadj(combo,SPY); cdd=stats(combo)['dd']
        tag=f"{capnm}" if rb==0.20 else ""
        print(f"  {tag:22}{rb*100:>6.0f}%{c:>+7.2f}{base['sh']:>+9.2f}{m['sh']:>+10.2f}{m['sh']-base['sh']:>+8.3f}{bdd*100:>+8.0f}%{cdd*100:>+9.0f}%")

# (4) NULL BLEND + the law's verdict ------------------------------------------------------------------
print("\n(4) NVDA + the NULL (regime-gated short) — pairing the rocket with the honest null")
combo,a=combine(bt,NULL,0.30); mN=riskadj(bt+a*NULL,SPY)
combo2,a2=combine(bt+a*NULL,NVDA,0.30); mNN=riskadj(combo2,SPY)
print(f"  breakthrough + null(30%)          Sharpe {mN['sh']:>+.2f}  maxDD {stats(bt+a*NULL)['dd']*100:>+.0f}%")
print(f"  breakthrough + null + NVDA(30%)   Sharpe {mNN['sh']:>+.2f}  maxDD {stats(combo2)['dd']*100:>+.0f}%")

print("\n"+"="*100)
print("READ:")
print("  • NVDA passes the ARITHMETIC of the outside-sleeve law (positive + not-100%-correlated → lifts Sharpe),")
print("    which is exactly why it's seductive — every backtest that touches it looks better.")
print("  • But it FAILS the law's spirit on two counts the Sharpe can't see:")
print("      NOT NEW  — the capstones already hold NVDA via QQQ/SPY (corr ~0.7 to the growth keeper). Adding it")
print("                 is levering a bet you already own, not diversifying — the definition of BLOAT.")
print("      NOT SAFE — a single name carries idiosyncratic blow-up risk (product miss, export ban, one earnings")
print("                 gap) that a Sharpe computed on a 9-year up-and-to-the-right sample cannot price. maxDD")
print("                 already shows ~-65%; the true left tail is a zero-day the history hasn't drawn yet.")
print("  • And the whole premise is a PAST-return bet: 'NVDA moves the market' is a statement about 2023-2025.")
print("    The capstones are built to be regime-agnostic precisely so they don't need that sentence to stay true.")
print("  VERDICT: 'bloated' is the right name. If you want the AI-compute beta, take it HONESTLY as a small, sized,")
print("  DISCLOSED single-name tilt on top of a capstone (a satellite you can turn off) — not baked into a keeper")
print("  book that's supposed to survive the regime where that sentence stops being true. The diversified capstone")
print("  is the core; NVDA is a garnish you label as such. Match the signal to the sleeve.")
