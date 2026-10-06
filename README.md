# Market Risk VaR and Expected Shortfall Backtesting

This project evaluates one-day market-risk estimates for a diversified ETF portfolio using Historical, Parametric Normal, and Monte Carlo Normal Value at Risk (VaR) and Expected Shortfall (ES). It moves from controlled data preparation to static model comparison and then to a 250-day rolling, one-day-ahead backtest. The emphasis is on transparent assumptions, reproducible controls, and interpretation appropriate for a junior market risk analyst portfolio.

**Stack:** Python, pandas, NumPy, SciPy, yfinance, Matplotlib, Seaborn, and Jupyter.

## Executive Summary

- At 95% confidence, all three rolling models produced breach rates near the theoretical 5% rate. Parametric Normal was closest at **5.05%**; its Kupiec, independence, and conditional-coverage tests all failed to reject at the 5% significance level.
- At 99%, both Normal models materially undercovered risk: Parametric Normal breached **2.32%** of days and Monte Carlo Normal **2.37%**, versus a theoretical 1%. Kupiec and conditional-coverage tests reject both models.
- Historical 99% VaR was closer in frequency at **1.44%**. Its Kupiec test does not reject unconditional coverage at 5%, but the independence and conditional-coverage tests reject, indicating that breaches were clustered rather than independently distributed.
- Monte Carlo Normal did not clearly improve on Parametric Normal. This is consistent with both models imposing essentially the same multivariate Normal distribution; simulation alone does not create richer tails.
- The worst realized loss was **6.59% on 2020-03-12**. All three 99% VaR forecasts were breached that day: Historical **2.45%**, Parametric Normal **1.61%**, and Monte Carlo Normal **1.58%**.

These results suggest that calibration at 95% was reasonable over this sample, while 99% tail coverage was more challenging. A failure to reject a statistical null does not prove that a model is correct, and the backtest is evidence about this portfolio, window, and historical period—not a production-model approval.

## Business Question

> Which one-day VaR model provides the most reliable risk coverage for a diversified ETF portfolio, and how do the models behave when volatility rises abruptly?

The analysis separates several related questions:

- Does each model produce the expected breach frequency at 95% and 99% confidence?
- Are breaches independent, or do they cluster during turbulent markets?
- How much loss severity remains beyond VaR, as summarized by ES?
- How does a 250-trading-day Historical model adjust when an extreme event enters the window?
- Do Normal Monte Carlo simulations improve tail behavior when their distributional assumption matches the Parametric Normal model?

## Portfolio and Data

| ETF | Exposure | Fixed weight |
|---|---|---:|
| SPY | U.S. large-cap equities | 40% |
| QQQ | U.S. technology-heavy equities | 25% |
| TLT | Long-duration U.S. Treasuries | 20% |
| GLD | Gold | 15% |

Prices come from Yahoo Finance through `yfinance`, using daily data, `auto_adjust=True`, and a download start parameter of `2018-01-01`. The valid adjusted-price sample runs from **2018-01-02 to 2026-09-21**; aligned simple returns run from **2018-01-03 to 2026-09-21** and contain 2,190 observations. The portfolio is modeled as daily rebalanced to constant weights. Transaction costs, turnover, taxes, and implementation frictions are excluded.

The frozen raw CSV contains one trailing date, `2026-09-22`, for which all four ETFs' Open, High, Low, and Close values are missing. Volume is non-zero on that date, but Volume does not establish price validity. The date is therefore excluded from price and return calculations without filling, interpolating, or overwriting the raw data.

The raw market-data CSV is intentionally ignored by Git and can be generated with [`src/download_data.py`](src/download_data.py). The processed returns, model results, and figures included here form a frozen analytical snapshot. A future download may differ because of later trading days, vendor revisions, corporate-action adjustments, or interface changes. See [`docs/data_notes.md`](docs/data_notes.md) for source details.

## Methodology

All models use simple daily returns and define positive loss as `loss = -portfolio_return`. VaR and ES are reported as positive one-day loss amounts.

- **Historical:** VaR is the empirical loss quantile using NumPy's explicit `method="linear"`; ES is the mean of observed losses at or above VaR. The approach reflects realized tail behavior but depends on the regimes and limited tail observations in its estimation window.
- **Parametric Normal:** VaR and ES use the sample mean and sample standard deviation (`ddof=1`) under a Normal return assumption. It is transparent and responsive to volatility, but symmetric thin tails may understate extreme losses.
- **Monte Carlo Normal:** Four-asset returns are simulated jointly from the rolling historical mean vector and covariance matrix, then aggregated using the fixed weights. The static study uses 100,000 paths. The rolling study uses 20,000 paths per forecast date, seed 42, and common random numbers for reproducibility. Because the simulated distribution remains Normal, close agreement with Parametric Normal is expected and is not independent validation.
- **Expected Shortfall:** ES measures the average loss at or beyond the VaR threshold. It complements breach-based VaR tests by describing tail severity, but this project does not perform a formal ES backtest.

## Backtesting Design

Each forecast uses the preceding **250 trading days** and predicts the next day's risk without look-ahead. The first forecast is **2019-01-02**, the last is **2026-09-21**, and the evaluation contains **1,940** one-day-ahead forecasts. A breach is recorded only when realized loss is strictly greater than VaR; equality is not a breach.

Expected breach probabilities are 5% at 95% confidence and 1% at 99%. Model diagnostics include:

- the Kupiec unconditional-coverage test for breach frequency;
- the Christoffersen independence test for breach clustering; and
- the Christoffersen conditional-coverage test combining frequency and independence.

The tests use asymptotic chi-square reference distributions. Their 99% results should be interpreted carefully because the expected breach count is only 19.4 and finite-sample behavior can matter.

## Static VaR and ES Results

The full-sample static estimates use 2,190 returns and an illustrative USD 1,000,000 portfolio.

| Model | Confidence | VaR | ES | VaR on USD 1m | ES on USD 1m |
|---|---:|---:|---:|---:|---:|
| Historical | 95% | 1.370% | 2.060% | $13,701 | $20,605 |
| Historical | 99% | 2.427% | 3.427% | $24,275 | $34,268 |
| Parametric Normal | 95% | 1.401% | 1.770% | $14,005 | $17,700 |
| Parametric Normal | 99% | 2.003% | 2.303% | $20,031 | $23,027 |
| Monte Carlo Normal | 95% | 1.398% | 1.766% | $13,983 | $17,660 |
| Monte Carlo Normal | 99% | 1.998% | 2.287% | $19,984 | $22,873 |

Historical 99% VaR and ES exceed both Normal-model estimates. This is consistent with the portfolio return sample's **8.71 excess kurtosis**, which indicates materially heavier tails than a Normal distribution. At 95%, however, both Normal VaRs are slightly above Historical VaR, so no model is uniformly most conservative. These static full-sample estimates illustrate model mechanics and risk levels; they are not out-of-sample validation.

![Static one-day VaR and ES comparison](outputs/figures/static_var_es_comparison.png)

## Rolling Backtest Results

| Model | Confidence | Expected breaches | Actual breaches | Actual rate | Kupiec | Independence | Conditional coverage |
|---|---:|---:|---:|---:|---|---|---|
| Historical | 95% | 97.0 | 110 | 5.67% | Do not reject (0.184) | Do not reject (0.472) | Do not reject (0.320) |
| Historical | 99% | 19.4 | 28 | 1.44% | Do not reject (0.066) | Reject (0.007) | Reject (0.005) |
| Parametric Normal | 95% | 97.0 | 98 | 5.05% | Do not reject (0.917) | Do not reject (0.630) | Do not reject (0.886) |
| Parametric Normal | 99% | 19.4 | 45 | 2.32% | Reject (<0.001) | Do not reject (0.107) | Reject (<0.001) |
| Monte Carlo Normal | 95% | 97.0 | 101 | 5.21% | Do not reject (0.679) | Do not reject (0.739) | Do not reject (0.868) |
| Monte Carlo Normal | 99% | 19.4 | 46 | 2.37% | Reject (<0.001) | Do not reject (0.120) | Reject (<0.001) |

Values in parentheses are p-values. “Do not reject” means the sample does not provide sufficient evidence against the relevant null at the 5% significance level; it does not establish that the model is correct.

![Actual versus theoretical VaR breach rates](outputs/figures/breach_rate_comparison.png)

The 99% rolling paths show different adaptation patterns. Historical VaR changes in steps as observations enter and leave the 250-day window, while the two Normal estimates move more gradually with rolling mean and volatility. The two Normal lines remain close because they share the same distributional assumption.

![Rolling one-day 99% VaR backtest](outputs/figures/rolling_var_backtest_99.png)

## Stress-Period Findings

The fixed stress-period labels are used only for ex-post evaluation; they do not enter model estimation:

- **COVID-19 sell-off, 2020-02-19 to 2020-04-30:** Historical recorded 14 breaches at 95% and 8 at 99%; each Normal model recorded 12 and 8. The 99% Historical threshold first reached 1.5 times its pre-period level on 2020-03-10, compared with 2020-03-12 for both Normal models. This timing reflects different updating mechanics, not proof of superior forecasting. Historical 99% VaR still had eight breaches during the period.
- **2022 tightening, 2022-01-03 to 2022-12-30:** 95% breach counts were 31 Historical, 31 Parametric Normal, and 32 Monte Carlo Normal. At 99%, the counts were 9, 16, and 16, respectively.

On the worst day, 2020-03-12, the realized 6.59% loss exceeded every 99% forecast. The gap was largest for the Normal models, whose thresholds were close to 1.6% before the shock.

![COVID-19 rolling 99% VaR response](outputs/figures/covid_var_backtest_zoom.png)

## Risk Management Interpretation

Parametric Normal provided the closest 95% breach frequency, and none of its 95% tests rejected. That supports its use as a transparent benchmark within this sample, subject to the limits of statistical power and model assumptions. At 99%, neither Normal approach delivered adequate unconditional or conditional coverage. Historical 99% VaR was closer to the target breach rate, but the rejected independence and conditional-coverage tests indicate clustered failures during stress.

For monitoring, the evidence supports separating three questions: frequency, independence, and severity. Breach counts alone would miss the Historical model's clustering problem; VaR alone would miss the size of losses after the threshold. A practical model review would therefore combine rolling coverage tests, ES or breach-severity monitoring, stress-period analysis, and investigation of market-data and regime changes. These results are analytical evidence, not investment advice or a regulatory capital determination.

## Limitations

- Constant daily rebalancing is assumed; transaction costs, turnover, taxes, liquidity, and execution constraints are excluded.
- The portfolio contains linear ETF exposures only and does not model options, nonlinear payoffs, intraday risk, or basis risk.
- A 250-day window is a convention, not the only reasonable choice; shorter and longer windows would change responsiveness and sampling error.
- A 99% Historical estimate from 250 observations relies on only about 2–3 tail observations and is sensitive to individual extremes.
- Normal models impose symmetric, thin-tailed returns despite observed excess kurtosis.
- Monte Carlo Normal is a simulation engine, not an independent tail model, because its distributional assumption matches Parametric Normal.
- The project does not perform a formal ES backtest or evaluate filtered historical simulation, EVT, GARCH, t-distributions, or regime-switching challengers.
- Kupiec and Christoffersen p-values use asymptotic reference distributions and can be fragile with small 99% breach counts.
- Yahoo Finance data may be revised, and future downloads may not reproduce this frozen snapshot exactly.

## Project Structure

```text
market-risk-var-es-backtesting-python/
├── data/
│   ├── raw/                       # Generated raw market data; CSV ignored by Git
│   └── processed/                 # Frozen asset and portfolio return series
├── docs/
│   ├── data_notes.md
│   └── project_reflection.md
├── notebooks/
│   ├── 01_data_and_portfolio_setup.ipynb
│   ├── 02_var_es_models.ipynb
│   └── 03_var_backtesting.ipynb
├── outputs/
│   ├── figures/                   # Eight exported analytical figures
│   └── tables/                    # Static and rolling result CSVs
├── src/
│   └── download_data.py
├── .gitignore
├── README.md
└── requirements.txt
```

## How to Run

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 src/download_data.py
python3 -m jupyter nbconvert --execute --to notebook --inplace notebooks/01_data_and_portfolio_setup.ipynb
python3 -m jupyter nbconvert --execute --to notebook --inplace notebooks/02_var_es_models.ipynb
python3 -m jupyter nbconvert --execute --to notebook --inplace notebooks/03_var_backtesting.ipynb
```

Run the notebooks in numerical order; each notebook is designed to execute from a fresh kernel. The committed processed data and outputs represent the documented frozen snapshot. Running the downloader today may produce a different raw file and therefore different downstream results. The downloader checks the expected columns, date order, duplicate dates, and missing Close values before saving the raw CSV.

Notebook workflow: [`01_data_and_portfolio_setup.ipynb`](notebooks/01_data_and_portfolio_setup.ipynb) → [`02_var_es_models.ipynb`](notebooks/02_var_es_models.ipynb) → [`03_var_backtesting.ipynb`](notebooks/03_var_backtesting.ipynb).

## Skills Demonstrated

- Market-data validation and reproducible data lineage
- Portfolio-return construction and alignment controls
- Historical, Parametric Normal, and multivariate Monte Carlo VaR/ES
- Rolling one-day-ahead forecasting without look-ahead bias
- Kupiec and Christoffersen backtesting
- Stress-period and breach-severity interpretation
- Reproducible notebooks, numerical assertions, and publication-ready figures

## Project Status

The three notebooks have been executed top to bottom, and their frozen outputs are included. The project is complete as an analyst portfolio study and ready for GitHub presentation within the documented scope. It is not presented as a production risk engine, regulatory model, trading strategy, or investment recommendation.

For design decisions, lessons learned, and possible extensions, see [`docs/project_reflection.md`](docs/project_reflection.md).
