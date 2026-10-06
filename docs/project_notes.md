# Project Notes

## Why I chose these three VaR approaches

I wanted to compare methods that start from different ideas but are still
simple enough to inspect closely.

Historical VaR uses the losses that actually occurred in the estimation
window. It does not require a return distribution, so it gives a useful view of
how recent market events affect the risk estimate. Its weakness is that it can
only reuse observations already in the sample, and a 99% estimate from 250 days
depends on very few tail observations.

Parametric Normal VaR is a clear benchmark. Once the rolling mean and standard
deviation are estimated, the VaR and ES calculations are direct. That makes it
easy to see what changes when volatility rises, but the Normal assumption is a
strong one for market returns with fat tails.

I included Monte Carlo because I wanted to understand joint simulation and how
the asset covariance matrix feeds into portfolio risk. The simulation draws
four correlated ETF returns and then applies the fixed portfolio weights. In
this version the simulated returns are still Normal, so Monte Carlo is not a
separate tail model. The point of the comparison was to observe how the methods
behave, not to select a single “best” model.

## What surprised me

The biggest lesson was that a model can look reasonable at 95% and still have a
clear problem at 99%. The three 95% breach rates ranged from 5.05% to 5.67%,
which is fairly close to the expected 5%. At 99%, Parametric Normal breached on
2.32% of days and Monte Carlo Normal on 2.37% of days, more than twice the
theoretical 1% rate. Their Kupiec and conditional-coverage tests rejected.

Historical 99% VaR looked better if I considered only the total number of
breaches. It recorded 28 breaches, or 1.44%, and the Kupiec test did not reject
unconditional coverage at the 5% level. However, the Christoffersen
independence test did reject. The timing of failures therefore changed the
conclusion: a breach rate closer to 1% did not mean that the breaches were well
spread through time.

I initially expected Monte Carlo to behave more differently from the
parametric model. After comparing the results, it became clear that simulation
itself does not create heavier tails when the simulated returns are still
Normal. The two methods produced similar VaR paths, breach rates, and test
decisions because they shared the same mean, covariance, and distributional
assumption.

The COVID period made these limits visible. On `2020-03-12`, the portfolio lost
6.59%, while the 99% forecasts were only 2.45% for Historical, 1.61% for
Parametric Normal, and 1.58% for Monte Carlo Normal. All three models were
breached on the same day even though they updated in different ways.

## Decisions I made

I kept the portfolio weights fixed at 40% SPY, 25% QQQ, 20% TLT, and 15% GLD.
This avoids mixing portfolio optimization with the model comparison. It also
makes every method evaluate the same equity, bond, and gold exposure.

I used a 250-trading-day window because it represents roughly one year of daily
observations and is common in simple VaR examples. It is long enough to estimate
a covariance matrix without difficulty, but short enough to show how risk
forecasts react when market conditions change. The trade-off is especially
important for Historical 99% VaR, where only about 2–3 observations sit in the
nominal tail.

The holding period is one day because the data are daily and it keeps the
forecast alignment clear. For every forecast date, the training window ends on
the previous trading day. I define a breach as `realized loss > VaR`; equality
is not counted. This strict rule is used consistently across models and
confidence levels.

COVID-19 and the 2022 tightening period are ex-post labels. They are used only
to summarize when breaches occurred and never enter the estimation windows. I
also separated the full-sample static estimates from the rolling backtest. The
static section is useful for comparing model mechanics and ES levels, while the
rolling section is the actual one-day-ahead forecast evaluation.

## What I would try next

I would first replace the Normal assumption with either a Student-t model or
filtered historical simulation and check whether 99% coverage improves without
making the 95% estimates unnecessarily conservative. I would also compare
shorter and longer rolling windows to see how much the conclusions depend on
the one-year choice.

A formal ES backtest would add a better test of loss severity beyond VaR.
Finally, I would run a compact sensitivity analysis covering window length,
random seed and simulation count, and the empirical quantile rule. Those steps
would extend the current comparison while keeping the same portfolio and
one-day-ahead design.
