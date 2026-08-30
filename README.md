# Blaque Baux Bloated

**An honest null. Bolt NVDA — the market's engine — onto the diversified capstones, and watch it *look* better while getting worse.**

Bloated is a member of the Blaque Baux family. The [core repo](https://github.com/blaquebaux/base) is the
**engine and blueprint** — a governed, systematic platform (Julia). Bloated inherits the family's *method* (causal
backtests, fat-tail scorecard, match-the-signal-to-the-sleeve) but **not** its live rails: the whole point of this
sleeve is that it should **never** be traded. It is published as a cautionary study, in the family's tradition of
keeping the red scorecards ([bear](https://github.com/blaquebaux/bear) is the other one).

> **Not investment advice.** Educational/research software. Nothing here is validated to real-money standard. See [DISCLAIMER](DISCLAIMER.md) and [LICENSE](LICENSE).

```bash
git clone --recursive https://github.com/blaquebaux/bloated.git
python3 research/bloated_1_nvidia_mix.py    # needs Alpaca SIP keys in the environment
```

## The thesis

NVDA is what's been moving the market. The capstones ([breakthrough](https://github.com/blaquebaux/breakthrough),
[brilliant](https://github.com/blaquebaux/brilliant), [bastion](https://github.com/blaquebaux/bastion)) don't hold
it *by name*. So the tempting move is obvious: bolt the market's engine onto the diversified allocators. Interesting,
or bloated? **Only analysis can tell — and it says bloated.**

The catch is that NVDA passes the *arithmetic* of the family's own [outside-sleeve
law](https://github.com/blaquebaux/breakthrough) — a satellite lifts a capstone iff it is **new, uncorrelated, and
positive-return**. NVDA is spectacularly positive and less-than-fully correlated, so it lifts every Sharpe it
touches. That is exactly what makes it dangerous. It passes the arithmetic and **fails the spirit** on the two
things a Sharpe cannot see.

## What the analysis found

[`research/bloated_1_nvidia_mix.py`](research/bloated_1_nvidia_mix.py) — causal, gross, Alpaca SIP daily, 2017–2026:

**(1) Standalone — the rocket and the crater under it**

| | Sharpe | CAGR | vol | maxDD | exKurt |
|---|---|---|---|---|---|
| NVDA | +1.17 | +58% | 50% | **−66%** | +5.2 |
| SPY | +0.87 | +15% | 18% | −34% | — |

The Sharpe is a monster because the *sample* is. The −66% is the tell — a single name can lose two-thirds and you
hold every point of it.

**(2) The capstones already own it**

| stream | corr(NVDA) | beta(NVDA) |
|---|---|---|
| QQQ (growth keeper) | **+0.77** | +0.36 |
| SPY (spine) | +0.68 | +0.25 |
| breakthrough | +0.56 | +0.10 |
| bastion | +0.52 | +0.08 |
| brilliant | +0.41 | +0.06 |

NVDA is a top QQQ holding and the growth keeper is ~0.77 correlated to it. "Adding" NVDA is not new exposure — it's
**levering a bet the book already holds.** That is the definition of bloat.

**(3) As a satellite it lifts Sharpe — and deepens the crater every time**

| capstone + NVDA (30% risk budget) | base Sharpe | combo Sharpe | ΔSharpe | base maxDD | combo maxDD |
|---|---|---|---|---|---|
| breakthrough | +1.17 | +1.27 | +0.107 | −17% | −20% |
| bastion | +1.24 | +1.34 | +0.106 | −13% | −16% |
| brilliant | +1.12 | +1.27 | +0.155 | −15% | −17% |

Every point of Sharpe is bought with more drawdown. Pairing it with the honest [bear](https://github.com/blaquebaux/bear)
null gives the prettiest headline (+1.36) and the least honesty — a broad short can't offset one name's tail.

## Why "bloated" is the right name

- **Not new.** corr +0.56 to breakthrough, +0.77 to the growth keeper. Adding NVDA levers a bet the book already
  owns — not diversification, redundancy.
- **Not safe.** One name carries idiosyncratic blow-up risk — an export ban, a product miss, one earnings gap — that
  a nine-year up-and-to-the-right sample cannot price. The −66% on record is *not* the true left tail.
- **A past-return bet.** "NVDA moves the market" is a statement about 2023–2025. The capstones are built
  regime-agnostic precisely so they don't depend on that sentence staying true.

## The counterweight studies — can anything outside QQQ fix it?

If NVDA's flaw is that it's already-owned tech beta, the obvious next question is: what *outside* the QQQ complex
counteracts it? Two follow-ups run that down, and both re-derive the family's own keepers.

**[`research/bloated_2_counterweight.py`](research/bloated_2_counterweight.py)** — nine candidates outside QQQ,
each blended 50/50 (risk-parity) with NVDA, ranked on whether the crater shrinks while the return survives:

| NVDA + … | Sharpe | ΔSh | CAGR | maxDD | verdict |
|---|---|---|---|---|---|
| **GLD** (gold) | +1.39 | **+0.21** | +55% | **−51%** | ✅ uncorrelated *and* pays you — the real counterweight |
| **MF-trend** (managed futures) | +1.26 | +0.09 | +47% | −49% | ✅ crisis-negative *and* positive carry |
| UUP (dollar) | +1.14 | −0.03 | +39% | −40% | haven — cuts DD most, but thin carry |
| DBC / XLF / IWD / XLE / EFA | +1.02–1.13 | negative | — | −57 to −66% | ❌ positive but too **equity-correlated** to offset a tech crater |
| TLT (long bonds) | +0.86 | **−0.32** | +26% | **−71%** | ❌ crisis-negative but zero carry → *deepens* the crater |

The dividing line: a counterweight must sit outside **equity beta**, not just outside the tech sector. Only **gold**
and **managed-futures trend** clear it — which is exactly the [cross-asset keeper book](https://github.com/blaquebaux/base)
and [balsamic](https://github.com/blaquebaux/balsamic)'s satellite. *Counterweighting NVDA back to sanity just
rebuilds a capstone around it.*

**[`research/bloated_3_inverse.py`](research/bloated_3_inverse.py)** — the tempting shortcut: buy the *perfect*
negative. PSQ (−1× QQQ), SQQQ (−3× QQQ), and YQQQ (inverse-QQQ with an income overlay) all deliver textbook
−1.00 / −0.94 correlation to QQQ — and all fail, because a perfect inverse is a perfect return-incinerator:

| | corr QQQ | Sharpe | CAGR | maxDD |
|---|---|---|---|---|
| PSQ (−1×) | −1.00 | −0.79 | −19% | −87% |
| SQQQ (−3×) | −1.00 | −0.85 | **−55%** | **−100%** |
| YQQQ (inverse+income)\* | −0.94 | — | −16%\* | −29%\* |

Two layers of negative carry — the **structural short** (you're short an asset with positive drift) and the
**daily-reset volatility decay** (each bleeds an extra ~3%/yr vs a naive continuous short). Every inverse blend
trades return for drawdown at a punishing rate; 50/50 PSQ collapses NVDA's Sharpe +1.17 → +0.57. The income overlay
on YQQQ softens the bleed but can't make a structural short pay. *(\*YQQQ lists only from 2024-08 — a short,
crash-free sample, flagged in the code; a weaker test than PSQ/SQQQ, not read as a full cycle.)*

Same lesson both ways: **uncorrelated is necessary, positive-return is not optional.** A short with negative carry
fails the [outside-sleeve law](https://github.com/blaquebaux/breakthrough) exactly as a tail hedge does. If you ever
want QQQ-crash protection *specifically*, it must be a small, timed, regime-gated overlay you turn off in up-regimes
(what [bastion](https://github.com/blaquebaux/bastion)'s bear overlay does) — never a buy-and-hold inverse line.

## The honest way to have the bet

If you want the AI-compute beta, take it **honestly**: a small, sized, *disclosed* single-name tilt on top of a
capstone — a garnish you can turn off — never baked into a keeper book that's supposed to survive the regime where
that sentence stops being true. The diversified capstone is the core; NVDA is a garnish you label as such.
**Match the signal to the sleeve.**

## Status
**Honest null — published as a cautionary study, deliberately NOT graduated to a live rail.** There is no `live/`
directory and no allocator, by design. The red scorecard is the point.

## Layout
```
engine/     the Blaque Baux platform (git submodule -> blaquebaux/base)
research/   bloated_1_nvidia_mix.py    — the NVDA-into-the-capstones study (the null)
            bloated_2_counterweight.py — what outside QQQ counteracts it (gold + trend = a capstone)
            bloated_3_inverse.py       — inverse QQQ (PSQ/SQQQ/YQQQ): perfect corr, worthless return
```

## The Blaque Baux family
This repo is one sleeve of the **Blaque Baux** family — a single governed engine steered in many directions. The
[core repo](https://github.com/blaquebaux/base) is the base/blueprint and holds the
[full family roster](https://github.com/blaquebaux/base#the-blaquebaux-family).

## License
[MIT](LICENSE). (c) 2026 Carter Warrens.
