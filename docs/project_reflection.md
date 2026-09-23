# Project Reflection

## Why I Chose This Project

I chose this project because VaR is a familiar headline measure, but a credible implementation requires much more than calculating a percentile. The useful question is whether a risk estimate behaves as intended when it is converted into a sequence of forecasts and confronted with realized losses. That made the project a good vehicle for demonstrating the combination of data controls, portfolio construction, statistical modeling, and model validation that I want to bring to a market risk analyst role.

The four-ETF portfolio was deliberately simple but economically varied. SPY and QQQ provide overlapping but distinct equity exposure, TLT adds long-duration government bonds, and GLD adds a non-equity diversifier. Fixed weights keep the interpretation focused on model behavior rather than portfolio optimization. The central question became: which one-day VaR model provides the most reliable coverage, and what happens when volatility rises sharply?

## Most Important Design Decisions

The first important decision was to establish one risk convention across every model: simple daily returns, positive loss defined as the negative of return, and one-day VaR and ES reported as positive loss amounts. This avoided a common sign error and made Historical, Parametric Normal, and Monte Carlo Normal results directly comparable.

I also separated the project into three stages. The first notebook owns data validation, price cleaning, return calculation, and the fixed-weight portfolio. The second presents static full-sample VaR and ES as a model-mechanics comparison. The third uses 250-day rolling windows to produce genuinely one-day-ahead forecasts before applying coverage and independence tests. This separation prevents a static in-sample estimate from being mistaken for evidence of forecast reliability.

For empirical quantiles, I made NumPy's `method="linear"` explicit rather than relying on a version-dependent default. A breach is strictly `actual_loss > VaR`, not greater than or equal to VaR. The Monte Carlo implementation uses a fixed seed and common random numbers, which makes repeated runs and date-to-date comparisons reproducible. These choices are small in code but important for auditability.

## What I Learned

The strongest lesson was that “closest breach rate” is not the same as “best model.” At 95%, Parametric Normal produced a 5.05% breach rate, very close to the theoretical 5%, and none of the three tests rejected. At 99%, however, both Normal models breached more than twice as often as expected: 2.32% for Parametric Normal and 2.37% for Monte Carlo Normal. Their unconditional and conditional coverage tests rejected.

Historical 99% VaR looked better on frequency at 1.44%, and its Kupiec test did not reject at 5%. Yet its independence and conditional-coverage tests did reject. That distinction matters: a model can have an acceptable aggregate exception count while still failing when exceptions arrive in clusters. “Do not reject” is also deliberately weaker than “accept” or “prove correct.”

The static analysis helped explain the 99% behavior. Portfolio returns had mild negative skewness of -0.099 but excess kurtosis of 8.714. Historical 99% VaR and ES were 2.427% and 3.427%, compared with about 2.00% and 2.30% for the Normal approaches. At 95%, the Normal VaRs were slightly higher than Historical VaR, so the evidence does not support a blanket statement that one method is always most conservative. ES also added information that VaR could not: it quantified average loss severity after the threshold was crossed.

## Technical Challenges

The most useful data-quality issue appeared at the end of the raw file. On `2026-09-22`, Open, High, Low, and Close were missing for all four ETFs, while Volume was non-zero. Volume does not establish price validity, so I treated the date as an invalid trailing market-data row and excluded it before calculating prices and returns. I did not fill missing OHLC values, interpolate them, or overwrite the raw CSV. This reinforced the importance of defining validity from the fields required by the calculation rather than from an adjacent field that happens to be populated.

Rolling estimation created a different challenge. Historical 99% VaR with a 250-day window has only about 2–3 observations in its nominal tail. The resulting estimate changes in visible steps and can be dominated by a small number of events. During the COVID-19 sell-off, the Historical 99% threshold increased faster by the project's 1.5-times diagnostic, but it still recorded eight 99% breaches. The Normal models updated more smoothly as volatility rose, yet their pre-shock thresholds were too low: on 2020-03-12, the 6.59% loss exceeded Historical 99% VaR of 2.45%, Parametric Normal VaR of 1.61%, and Monte Carlo Normal VaR of 1.58%.

I also learned that simulation sophistication should not be confused with distributional sophistication. Monte Carlo Normal and Parametric Normal were close because they shared the same Normal assumption. The simulation framework is flexible, but in this implementation it did not add fat tails, volatility dynamics, or a new source of model robustness.

## What I Would Improve Next

My next step would be to add challenger models rather than tune the current models until they pass. Useful extensions include a Student-t specification, filtered historical simulation, exponentially weighted volatility, GARCH-based forecasts, and an EVT treatment of the far tail. I would compare several rolling-window lengths and use sensitivity analysis to show the trade-off between responsiveness and parameter stability.

I would also strengthen validation with finite-sample or bootstrap versions of the coverage tests, especially at 99%, and add a formally justified ES backtest. For a production-oriented extension, I would include data-vendor reconciliation, stale-price and corporate-action controls, model inventory metadata, exception escalation rules, and monitoring of input and output drift. If the portfolio included options, I would replace the linear return aggregation with full revaluation or appropriate delta-gamma methods and incorporate liquidity horizons.

## Relevance to My Career Direction

This project reflects the kind of work I want to do in market risk: connect a clear risk definition to controlled data, implement several models transparently, test forecasts rather than relying on in-sample fit, and communicate limitations without hiding behind model complexity. It also demonstrates that I can distinguish statistical evidence from business interpretation. A 95% model that does not fail a test is not automatically safe, a 99% model with a closer breach count may still have clustered exceptions, and a Monte Carlo label does not guarantee a better tail model.

The final result is intentionally an analyst portfolio project rather than a claim of production readiness. Its value is the reasoning chain: validated inputs, explicit assumptions, reproducible calculations, independent checks, clear visual evidence, and conclusions calibrated to what the sample can actually support.
