# Data Notes

## Source and project snapshot

The project uses daily prices from Yahoo Finance, downloaded with `yfinance` for
SPY, QQQ, TLT, and GLD. The download starts at `2018-01-01`, uses a one-day
interval, and sets `auto_adjust=True`. This means the OHLC prices returned by
`yfinance` are adjusted for events such as splits and distributions. The
analysis uses the adjusted `Close` field to calculate simple daily returns.

The raw project snapshot runs from `2018-01-02` through `2026-09-22`. The first
date reflects the first trading day available after the requested start date.
The raw CSV is saved as `data/raw/etf_prices.csv`; it is not committed to Git.
The two processed return files and the result files are committed so the
reported analysis remains tied to one fixed sample.

The download script checks that the expected four ETFs and five OHLCV fields
are present. It also checks that dates are ordered and unique, reports missing
`Close` values, and flags dates where all four ETFs have no valid closing
price. It does not fill missing prices.

## The trailing 2026-09-22 row

In the saved snapshot, `2026-09-22` has missing Open, High, Low, and Close
values for all four ETFs. Volume is present, but a non-zero volume value is not
enough to calculate a valid return when the price fields are missing.

Notebook 01 therefore removes this row in memory before selecting adjusted
closes. The raw file itself is left unchanged. The latest valid price date is
`2026-09-21`, leaving 2,191 valid price observations and 2,190 aligned daily
return observations from `2018-01-03` through `2026-09-21`.

## Why a future download may differ

Running the script later may add trading days or return slightly different
historical values. Yahoo Finance can revise data, corporate-action adjustments
can change, and `yfinance` may change how it formats the downloaded columns.
Package versions used by this project are listed in `requirements.txt`, but
pinning the Python packages cannot freeze the upstream market-data source.

For that reason, the committed tables and figures should be read as results
from this project snapshot. A deliberate data refresh should be followed by
running all three notebooks in order and checking how the new sample changes
the reported results.
