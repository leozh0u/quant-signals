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

---

## H2: H1's negative result was an artifact of the tiny cross-section (status: registered)

Claim: the same 20d momentum long-short, run on ~100 names (the current S&P 100), clears H1's kill line. Registered because H1's most defensible objection is that 2 names per leg is noise, so the small universe has to be ruled out before momentum at this horizon is called dead.

Horizon, test, kill line: identical to H1, universe swapped for universe.txt minus ETFs. Same script (`experiments/momentum.py --universe universe.txt`).

Known bias, stated up front: the universe is today's index membership, so the panel is survivorship biased. That inflates long-side returns generally; it has no obvious reason to rescue a cross-sectional long-short specifically, but any positive result would need re-checking on point-in-time membership before being believed.

Result (2026-07-13, `experiments/momentum.py --universe universe.txt`): still dead, and the small universe was not the problem. On 99 names, gross Sharpe is -0.49 with the per-year sign negative in 25 of 27 years; net lands at -1.40, exactly the turnover-matched null's p95, which fails the strict kill line. So H1's objection is answered: more breadth made momentum look worse, not better.

The actual finding is the sign. Persistent negative gross Sharpe on a momentum book means the opposite book has persistent positive gross Sharpe: 20d returns mean-revert in this panel, which matches the short-term reversal literature. That observation is data-snooped (it comes from looking at H2's result), so it gets its own registration as H3 rather than a quiet victory lap.

---

## H3: Short-term reversal exists gross but dies to costs (status: supported)

Claim: flipping the H2 book (long the bottom 20d-return quintile, short the top) gives positive gross Sharpe on the ~100-name universe, and net Sharpe after 10 bps per side still fails the kill line. The literature says reversal is real and costs eat it; this registration predicts BOTH halves, so there are two ways to be wrong.

Honesty note: H3 is motivated by H2's data, i.e. it is snooped and its evidence weight is discounted accordingly. Registered before running via `experiments/momentum.py --universe universe.txt --flip`. Same kill line as H1/H2 for the net claim.

Result (2026-07-13): supported on both halves. Gross Sharpe +0.49 (9.6%/yr), well above the null; net Sharpe -0.42 (-8.3%/yr) at 179x/yr turnover, so costs consume the edge entirely, which is the kill line's second clause even though the net number technically beats the null's p95 (the script's verdict line only checks the first clause; the writeup governs). This is the textbook fate of daily-rebalanced short-term reversal: a real effect that only someone with near-zero marginal costs can harvest.

What would change the verdict: slower rebalancing (hold the book for a week), tighter entry (trade only extreme deciles), or a cost model showing sub-2 bps effective costs. Any of those is a new hypothesis, registered before testing, and the first two are the obvious H4 candidates. Standing caveat from H2 applies: survivorship-biased universe.
