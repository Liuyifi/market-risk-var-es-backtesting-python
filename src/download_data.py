"""Download daily adjusted ETF prices from Yahoo Finance."""

from pathlib import Path

import pandas as pd
import yfinance as yf


TICKERS = ("SPY", "QQQ", "TLT", "GLD")
PRICE_FIELDS = ("Open", "High", "Low", "Close", "Volume")
START_DATE = "2018-01-01"
OUTPUT_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "raw" / "etf_prices.csv"
)


def validate_prices(prices: pd.DataFrame) -> pd.DatetimeIndex:
    """Run the checks needed before saving the downloaded prices."""
    if prices.empty:
        raise RuntimeError("Yahoo Finance returned no data.")

    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Expected downloaded data to use a DatetimeIndex.")
    if prices.index.has_duplicates:
        raise ValueError("Downloaded data contains duplicate dates.")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("Downloaded dates are not in increasing order.")

    if not isinstance(prices.columns, pd.MultiIndex) or prices.columns.nlevels != 2:
        raise ValueError("Expected two column levels: price field and ETF ticker.")

    expected_columns = {
        (field, ticker) for field in PRICE_FIELDS for ticker in TICKERS
    }
    actual_columns = set(prices.columns)
    missing_columns = sorted(expected_columns - actual_columns)
    if missing_columns:
        raise ValueError(f"Missing expected price columns: {missing_columns}")

    close_prices = prices["Close"].reindex(columns=TICKERS)
    print("Missing Close values by ETF:")
    print(close_prices.isna().sum().to_string())

    all_close_missing = close_prices.isna().all(axis=1)
    trailing_invalid_dates = prices.index[all_close_missing]
    if len(trailing_invalid_dates):
        first_invalid_position = prices.index.get_loc(trailing_invalid_dates[0])
        if not all_close_missing.iloc[first_invalid_position:].all():
            raise ValueError("All-ETF missing Close dates are not limited to the end.")

    valid_close_prices = close_prices.loc[~all_close_missing]
    if valid_close_prices.isna().any().any():
        missing_dates = valid_close_prices.index[
            valid_close_prices.isna().any(axis=1)
        ]
        formatted_dates = ", ".join(date.date().isoformat() for date in missing_dates)
        raise ValueError(f"Found internal missing Close values on: {formatted_dates}")

    return trailing_invalid_dates


def main() -> None:
    prices = yf.download(
        tickers=list(TICKERS),
        start=START_DATE,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    trailing_invalid_dates = validate_prices(prices)
    if len(trailing_invalid_dates):
        formatted_dates = ", ".join(
            date.date().isoformat() for date in trailing_invalid_dates
        )
        print(f"Trailing dates with no valid Close prices: {formatted_dates}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(OUTPUT_PATH)

    print(f"Date range: {prices.index.min().date()} to {prices.index.max().date()}")
    print(f"Rows: {len(prices):,}")
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
