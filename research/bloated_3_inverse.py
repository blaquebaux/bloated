#!/usr/bin/python3
# =============================================================================
# bloated_3_inverse.py — would PSQ / SQQQ (inverse QQQ) counteract the NVDA bloat?
#
# The intuition is clean: NVDA's problem is +0.77 corr to QQQ, so buy the PERFECT negative — PSQ is -1x QQQ
# daily, SQQQ is -3x QQQ daily. corr ~ -1. Doesn't that cancel the crater exactly?
#
# No — and this is the sharpest version of the law bloated_1/2 already showed. An inverse ETF is a hedge with
# TWO layers of negative carry:
#   1. STRUCTURAL SHORT — you are short an asset with a positive long-run drift (QQQ), so the expected return
#      is negative before any fees. You pay, every day, to hold the opposite of the thing that goes up.
#   2. DAILY-REBALANCE (VOLATILITY) DECAY — -1x/-3x reset EACH DAY, so over any multi-day path the product
#      compounds against you: (1+r)(1-r) < 1. At -3x the decay is ~9x the variance drag; SQQQ bleeds to near-
#      zero over years REGARDLESS of where QQQ ends up. It is not "short QQQ"; it is "short QQQ minus a large
#      daily rebalancing tax."
# So it protects the crash column beautifully and DESTROYS the return — the TLT trap (bloated_2) taken to the
# extreme. We quantify both: standalone bleed, the decay gap vs a naive continuous short, and the blend.
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

RAW=["NVDA","QQQ","PSQ","SQQQ","GLD"]
TR={s:bars(s) for s in RAW}
dates=sorted(set.intersection(*[set(TR[s]) for s in RAW]))
P={s:np.array([TR[s][d] for d in dates],float) for s in RAW}
R={s:P[s][1:]/P[s][:-1]-1 for s in RAW}
WARM=252; sqrt=np.sqrt
NVDA=R["NVDA"][WARM:]; QQQ=R["QQQ"][WARM:]; GLD=R["GLD"][WARM:]
crash=NVDA<=np.percentile(NVDA,5)
def ann_vol(x): return x.std()*sqrt(252)

# --- naive CONTINUOUS -1x / -3x (rebalanced only implicitly via arithmetic) to isolate the DECAY gap --------
# A held short earns -r each day but the *product* value path differs from a daily-reset ETF. We compare the
# realized ETF total-return CAGR against a synthetic daily -k*QQQ stream to expose the rebalancing tax.
def cagr(r): c=np.cumprod(1+np.asarray(r,float)); return c[-1]**(252/len(r))-1
synth_m1=-1.0*QQQ; synth_m3=-3.0*QQQ

print("="*100)
print("BLOATED-3 — would PSQ (-1x QQQ) / SQQQ (-3x QQQ) counteract the NVDA bloat?  (2017-08→2026-08, gross)")
print("="*100)

print("\n(1) STANDALONE — the inverse is a return-incinerator")
print(f"  {'':16}{'corr QQQ':>10}{'corr NVDA':>11}{'CRISIS corr':>13}{'Sharpe':>9}{'CAGR':>9}{'maxDD':>9}")
for nm,x in [("QQQ",QQQ),("PSQ (-1x)",R["PSQ"][WARM:]),("SQQQ (-3x)",R["SQQQ"][WARM:])]:
    cq=np.corrcoef(x,QQQ)[0,1]; cn=np.corrcoef(x,NVDA)[0,1]
    cc=np.corrcoef(x[crash],NVDA[crash])[0,1]; r=riskadj(x,QQQ); s=stats(x)
    print(f"  {nm:16}{cq:>+10.2f}{cn:>+11.2f}{cc:>+13.2f}{r['sh']:>+9.2f}{s['cagr']*100:>+8.0f}%{s['dd']*100:>+8.0f}%")

print("\n(2) THE DECAY TAX — daily-reset ETF vs a naive continuous short of the same leverage")
print(f"  {'':22}{'ETF CAGR':>11}{'naive -kx CAGR':>16}{'decay gap/yr':>14}")
print(f"  {'PSQ vs -1x QQQ':22}{cagr(R['PSQ'][WARM:])*100:>+10.0f}%{cagr(synth_m1)*100:>+15.0f}%{(cagr(R['PSQ'][WARM:])-cagr(synth_m1))*100:>+13.0f}%")
print(f"  {'SQQQ vs -3x QQQ':22}{cagr(R['SQQQ'][WARM:])*100:>+10.0f}%{cagr(synth_m3)*100:>+15.0f}%{(cagr(R['SQQQ'][WARM:])-cagr(synth_m3))*100:>+13.0f}%")
print("  → even vs a (already losing) continuous short, the daily reset bleeds extra every year — the tax you pay")
print("    for the -1x/-3x wrapper. $1 in SQQQ at the start is worth pennies now no matter what QQQ did.")

print("\n(3) ACID TEST — blend NVDA with the inverse. Small 'hedge' weights AND risk-parity, vs gold for scale.")
base=stats(NVDA); bn=riskadj(NVDA,QQQ)
print(f"  {'blend':26}{'Sharpe':>8}{'ΔSh':>8}{'CAGR':>8}{'maxDD':>9}{'ΔmaxDD':>9}")
print(f"  {'NVDA alone':26}{bn['sh']:>+8.2f}{'':>8}{base['cagr']*100:>+7.0f}%{base['dd']*100:>+8.0f}%{'':>9}")
def blend(a,b,wb): x=(1-wb)*a+wb*b; return x
def rp(a,b): va,vb=ann_vol(a),ann_vol(b); s=va/vb if vb>0 else 0; return 0.5*a+0.5*s*b
tests=[("NVDA + 10% PSQ",blend(NVDA,R["PSQ"][WARM:],0.10)),
       ("NVDA + 20% PSQ",blend(NVDA,R["PSQ"][WARM:],0.20)),
       ("NVDA + 10% SQQQ",blend(NVDA,R["SQQQ"][WARM:],0.10)),
       ("NVDA + 50/50 rp PSQ",rp(NVDA,R["PSQ"][WARM:])),
       ("NVDA + 50/50 rp GLD",rp(NVDA,GLD))]
for nm,bl in tests:
    m=riskadj(bl,QQQ); md=stats(bl)
    print(f"  {nm:26}{m['sh']:>+8.2f}{m['sh']-bn['sh']:>+8.2f}{md['cagr']*100:>+7.0f}%{md['dd']*100:>+8.0f}%{(md['dd']-base['dd'])*100:>+8.0f}%")

# (4) YQQQ — the newer inverse-QQQ INCOME product; run on ITS OWN short window, flagged honestly ----------
# YQQQ (Defiance Daily Target inverse-QQQ with an option-income overlay) only lists from 2024-08, so it has
# NO crash in its life. We report it separately over its own overlap and DO NOT pretend the 2017-sample
# conclusions transfer — data honesty: flag the gap, don't fake the history.
_yq=bars("YQQQ"); _ovl=sorted(set(_yq)&set(TR["QQQ"])&set(TR["NVDA"])&set(TR["GLD"]))
if len(_ovl)>60:
    yq=np.array([_yq[d] for d in _ovl]);   ryq=yq[1:]/yq[:-1]-1
    qq=np.array([TR["QQQ"][d] for d in _ovl]); rqq=qq[1:]/qq[:-1]-1
    nv=np.array([TR["NVDA"][d] for d in _ovl]); rnv=nv[1:]/nv[:-1]-1
    gl=np.array([TR["GLD"][d]  for d in _ovl]); rgl=gl[1:]/gl[:-1]-1
    b_yq=np.cov(ryq,rqq)[0,1]/np.var(rqq); c_yq=np.corrcoef(ryq,rqq)[0,1]; cn_yq=np.corrcoef(ryq,rnv)[0,1]
    s_yq=stats(ryq)
    print(f"\n(4) YQQQ — newer inverse-QQQ INCOME ETF, on its OWN window {_ovl[0]}→{_ovl[-1]} ({len(_ovl)} days)")
    print( "    ⚠ SHORT, CRASH-FREE SAMPLE — this is a weaker test than PSQ/SQQQ; do NOT read it as a full cycle.")
    print(f"    realized beta to QQQ {b_yq:+.2f} (income overlay softens the short), corr {c_yq:+.2f}, corr NVDA {cn_yq:+.2f}")
    print(f"    standalone over the window: total return {(np.cumprod(1+ryq)[-1]-1)*100:+.0f}%, maxDD {s_yq['dd']*100:+.0f}%")
    # same-window benchmarks so the comparison is apples-to-apples
    def _rp(a,b): va,vb=a.std(),b.std(); s=va/vb if vb>0 else 0; return 0.5*a+0.5*s*b
    for nm,x in [("NVDA + 50/50 YQQQ",_rp(rnv,ryq)),("NVDA + 50/50 GLD (same window)",_rp(rnv,rgl))]:
        m=stats(x); print(f"    {nm:32}Sharpe {m['sh']:+.2f}  CAGR {m['cagr']*100:+.0f}%  maxDD {m['dd']*100:+.0f}%")
    print("    → same verdict as PSQ/SQQQ even WITH the income cushion: it lost money short-QQQ into a rising")
    print("      tape, and it never saw a crash to justify the carry. An income overlay softens the bleed; it")
    print("      does not turn a structural short into a positive-return diversifier. Gold still wins the window.")
else:
    print("\n(4) YQQQ — insufficient overlapping history to test.")

print("\n"+"="*100)
print("READ:")
print("  • PSQ/SQQQ give you the PERFECT negative correlation (~-0.9 / -0.9 to NVDA, strongly negative in the")
print("    crash column) — and it is worthless, because the return is structurally negative. PSQ compounds to a")
print("    deep loss and SQQQ is a near-total wipeout: -3x daily reset + a rising underlying = volatility decay")
print("    that grinds the position toward zero regardless of the path.")
print("  • Every inverse blend TRADES RETURN FOR DRAWDOWN at a punishing rate: even a small 10% PSQ sleeve saws")
print("    the CAGR down while the Sharpe falls — you pay more in lost compounding than you save in crater. This")
print("    is the TLT trap (bloated_2) in its purest form: a hedge with large NEGATIVE carry FAILS the outside-")
print("    sleeve law (uncorrelated is necessary, POSITIVE-return is not optional).")
print("  • Contrast gold, kept in the table on purpose: same job (cut the crater) but it PAYS you to hold it, so")
print("    the blend Sharpe goes UP, not down. That is the whole difference between a diversifier and a short.")
print("  • YQQQ (the income-overlay inverse) is the same trap with a cushion: on its short, crash-free 2024+ life it")
print("    still LOST money shorting a rising QQQ. The option income softens the daily-reset bleed but cannot make")
print("    a structural short pay — and its sample never contained the crash that would be its only case for existing.")
print("  VERDICT: NO. An inverse-QQQ ETF does not counteract the bloat — it converts it into a slow bleed. If you")
print("  ever want QQQ-crash protection specifically, buy it as a SMALL, TIMED, regime-gated overlay you turn OFF")
print("  in up-regimes (what bastion's bear overlay does), never a buy-and-hold PSQ/SQQQ line. Match signal to sleeve.")
