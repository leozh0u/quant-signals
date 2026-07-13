# Hypotheses

Each signal idea gets an entry here before any code tests it. The entry states the claim, the horizon, the evaluation, and what would count as failure. Results get filled in after the test and are never edited afterward; corrections go in a new entry.

Format:

```
## H<n>: <name>            (status: registered | testing | supported | dead)
Claim:      ...
Horizon:    ...
Test:       ...
Kill line:  what result kills it
Result:     filled in after
```

---

## H1: Short-term momentum persists after costs (status: dead)

Claim: A cross-sectional momentum signal (past 20-day return, top vs bottom quintile) has positive net Sharpe on daily-rebalanced US large caps.

Horizon: 1 to 5 trading days.

Test: Walk-forward, 2 years train / 6 months test, rolled forward. 10 bps per side cost assumption. Compare against buy-and-hold and a random signal with the same turnover.

Kill line: Net Sharpe below the random-signal baseline's 95th percentile, or a gross edge that costs eat entirely.

Result (2026-07-13, `experiments/h1_momentum.py`): dead, and not even by costs. Gross Sharpe is -0.01 over 2000-2026 on the 10-stock universe, so there is no edge for costs to eat; at 187x/yr turnover the 10 bps assumption then takes net to -0.41, right at the turnover-matched random null's median (-0.43, p95 -0.16). Per-year net Sharpe flips sign constantly, so no sub-period story survives either. Buy-and-hold equal weight did 0.96 net over the same window, which mostly says these 10 mega caps went up for 26 years.

Caveats that keep this from being a claim about momentum generally: 10 large caps is a tiny cross-section (quintile = 2 names per leg), and 20d/daily-rebalance is the noisiest corner of the momentum literature. The run did its real job, which was exercising the backtester end to end: the null distribution centering near the signal, and turnover matching moving p95 from absurd to plausible, are both behaviors that would have exposed engine bugs.
