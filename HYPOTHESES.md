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

## H1: Short-term momentum persists after costs (status: registered)

Claim: A cross-sectional momentum signal (past 20-day return, top vs bottom quintile) has positive net Sharpe on daily-rebalanced US large caps.

Horizon: 1 to 5 trading days.

Test: Walk-forward, 2 years train / 6 months test, rolled forward. 10 bps per side cost assumption. Compare against buy-and-hold and a random signal with the same turnover.

Kill line: Net Sharpe below the random-signal baseline's 95th percentile, or a gross edge that costs eat entirely.

Result: not yet run. This is mostly a plumbing test for the backtester; the literature says daily-horizon momentum after costs is roughly a coin flip, which makes it a good honesty check. If the backtester reports something amazing here, the backtester is probably wrong.
