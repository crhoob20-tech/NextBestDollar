# MNQ Strategy Research — Six-Month Results

Automated run completed successfully on the `mnq-research` branch.

## Data window

**2026-03-26 through 2026-09-25** using the public NAS100 one-minute OHLCV proxy. The public source does not yet include the final requested Sep. 26–Oct. 2 sessions, so those sessions are not fabricated or inferred.

This is a comparative research backtest, not a broker-grade CME MNQ fill simulation. Approximate dollar results use the MNQ $2/index-point multiplier and $4 estimated round-trip friction.

## Scorecard

| Strategy | Trades | Win rate | Exp. R/trade | Profit factor | Total R | Max DD (R) | Approx. net, 1 MNQ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 4/4 Regime Pullback | 8 | 62.5% | +0.484 | 2.29 | +3.87R | 2.0R | +$360 |
| Open Drive | 28 | 50.0% | **+0.981** | **2.97** | **+27.46R** | **3.0R** | **+$5,371** |
| BOS Structural Retrace | 216 | 50.9% | +0.069 | 1.14 | +15.0R | 12.6R | -$11 |
| Major-Level Rejection | 89 | 46.1% | +0.152 | 1.28 | +13.5R | 8.0R | +$14 |
| All sleeves, unfiltered portfolio | 341 | 49.9% | +0.175 | 1.35 | +59.83R | 14.44R | +$5,734 |

## Main conclusion

**Open Drive is the only sleeve that currently looks strong enough to promote to the next research stage.** It produced the highest expectancy and profit factor while keeping drawdown modest and providing substantially more trades than the 4/4 model.

The 4/4 Regime Pullback remains valuable as a rare high-conviction setup, but eight trades in roughly six months is not enough to use as the sole trading strategy.

The high-frequency BOS sleeve generated positive R before dollar friction but was approximately flat/slightly negative after the current MNQ cost assumption. That is a warning that a high-frequency NQ idea may not translate economically to a single MNQ contract.

The Major-Level Rejection sleeve was positive in R but almost flat in estimated dollars and showed significant month-to-month regime sensitivity. It remains a research challenger, not a production strategy.

## Open Drive stress test

Open Drive's headline result is partly boosted by scheduled macro-event sessions, so it was stress-tested rather than accepted at face value.

### All 28 trades
- Total: +27.46R
- Expectancy: +0.981R/trade
- Profit factor: 2.97
- Approx. net: +$5,371 per 1 MNQ

### Normal days only — excluding tagged CPI/PPI/NFP/PCE/FOMC days
- 23 trades
- Total: +8.04R
- Expectancy: **+0.349R/trade**
- Profit factor: **1.58**
- Approx. net: **+$1,821 per 1 MNQ**

This matters: the strategy remained positive when the tagged high-impact macro days were removed.

### Remove the single largest winner
- 27 trades
- Total: +19.56R
- Expectancy: +0.724R/trade
- Profit factor: 2.40
- Approx. net: +$3,758

### Remove the three largest winners
- 25 trades
- Total: +8.97R
- Expectancy: **+0.359R/trade**
- Profit factor: **1.64**
- Approx. net: **+$2,322**

Therefore the positive result is not solely explained by one extreme trade. However, the 28-trade sample is still too small to call the edge proven.

## Monthly Open Drive results

| Month | Trades | Total R | Approx. net |
|---|---:|---:|---:|
| Apr 2026 | 3 | +3.37R | +$394 |
| May 2026 | 7 | +3.46R | +$572 |
| Jun 2026 | 5 | +7.47R | +$1,676 |
| Jul 2026 | 4 | -0.60R | -$189 |
| Aug 2026 | 5 | +6.51R | +$1,954 |
| Sep 2026 | 4 | +7.25R | +$964 |

Five of six tested calendar months were positive. July was negative.

## News observation

Five Open Drive trades occurred on the current high-impact-event tags and all five were profitable in this proxy sample, creating +19.42R. That is unusually strong and should **not** be assumed to persist. The correct next test is not to ban news automatically, but to split Open Drive into normal-day and event-day submodels and validate both on older futures data.

## Next research stage

1. Keep 4/4 rules frozen as the high-conviction sleeve.
2. Promote Open Drive to primary candidate.
3. Do not promote BOS or Major-Level Rejection yet.
4. Re-run exact rules on true CME NQ/MNQ one-minute data with contract-roll handling.
5. Extend Open Drive to at least 2–3 years and perform walk-forward/year-by-year analysis.
6. Build a paper-trading signal router only after that validation.
7. Live brokerage execution remains disabled until paper results agree with research results.
