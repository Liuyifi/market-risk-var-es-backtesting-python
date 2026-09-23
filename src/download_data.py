"""Download and safely persist daily adjusted ETF prices from Yahoo Finance."""

from pathlib import Path
import tempfile
from typing import Optional

import pandas as pd
import yfinance as yf


TICKERS = ("SPY", "QQQ", "TLT", "GLD")
START_DATE = "2018-01-01"
PRICE_FIELDS = ("Open", "High", "Low", "Close", "Volume")
PRICE_VALIDITY_FIELDS = ("Open", "High", "Low", "Close")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "etf_prices.csv"


def _validate_and_select(
    prices: pd.DataFrame,
) -> tuple[pd.DataFrame, int, int, pd.DatetimeIndex]:
    """Validate a multi-ticker OHLCV frame without filling missing prices."""
    if prices.empty:
        raise RuntimeError("Yahoo Finance returned an empty dataset.")

    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Expected a DatetimeIndex for downloaded prices.")
    if prices.index.isna().any():
        raise ValueError("Downloaded prices contain missing dates.")
    if prices.index.has_duplicates:
        duplicate_count = int(prices.index.duplicated(keep=False).sum())
        raise ValueError(f"Found {duplicate_count} rows with duplicate dates.")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("Downloaded dates are not in increasing order.")

    if not isinstance(prices.columns, pd.MultiIndex) or prices.columns.nlevels != 2:
        raise ValueError(
            "Expected exactly two column-header levels for a multi-ticker download, "
            f"but received {type(prices.columns).__name__} with "
            f"{getattr(prices.columns, 'nlevels', 1)} level(s)."
        )
    if prices.columns.has_duplicates:
        duplicates = prices.columns[prices.columns.duplicated()].tolist()
        raise ValueError(f"Downloaded data contain duplicate columns: {duplicates}")

    ticker_level = next(
        (
            level
            for level in range(prices.columns.nlevels)
            if set(TICKERS).issubset(set(prices.columns.get_level_values(level)))
        ),
        None,
    )
    field_level = next(
        (
            level
            for level in range(prices.columns.nlevels)
            if set(PRICE_FIELDS).issubset(set(prices.columns.get_level_values(level)))
        ),
        None,
    )
    if ticker_level is None or field_level is None or ticker_level == field_level:
        raise ValueError(
            "Downloaded columns do not contain the expected ETF and OHLCV levels. "
            f"Columns received: {prices.columns.tolist()}"
        )

    selected_columns = [
        column
        for column in prices.columns
        if column[ticker_level] in TICKERS
        and column[field_level] in PRICE_FIELDS
    ]
    selected = prices.loc[:, selected_columns]

    issues: list[str] = []
    for ticker in TICKERS:
        missing_fields = [
            field
            for field in PRICE_FIELDS
            if not any(
                column[ticker_level] == ticker and column[field_level] == field
                for column in selected.columns
            )
        ]
        if missing_fields:
            issues.append(f"{ticker}: missing fields {missing_fields}")
    if issues:
        raise ValueError("ETF integrity validation failed: " + "; ".join(issues))

    def get_series(ticker: str, field: str) -> pd.Series:
        matching = [
            column
            for column in selected.columns
            if column[ticker_level] == ticker and column[field_level] == field
        ]
        if len(matching) != 1:
            raise ValueError(
                f"Expected one {field} column for {ticker}, found {len(matching)}."
            )
        return selected[matching[0]]

    for ticker in TICKERS:
        for field in PRICE_VALIDITY_FIELDS:
            if get_series(ticker, field).notna().sum() == 0:
                issues.append(f"{ticker}: {field} is entirely missing")
    if issues:
        raise ValueError("ETF integrity validation failed: " + "; ".join(issues))

    close_prices = pd.DataFrame(
        {ticker: get_series(ticker, "Close") for ticker in TICKERS},
        index=selected.index,
    )
    valid_ranges = {}
    for ticker in TICKERS:
        valid_close = close_prices[ticker].dropna()
        if valid_close.empty:
            issues.append(f"{ticker}: Close has no valid first or last date")
        else:
            valid_ranges[ticker] = (valid_close.index[0], valid_close.index[-1])
    if issues:
        raise ValueError("ETF integrity validation failed: " + "; ".join(issues))

    if len(set(valid_ranges.values())) != 1:
        formatted_ranges = ", ".join(
            f"{ticker}={start.date().isoformat()}..{end.date().isoformat()}"
            for ticker, (start, end) in valid_ranges.items()
        )
        raise ValueError(
            "ETF integrity validation failed: valid Close date ranges differ: "
            + formatted_ranges
        )

    all_close_missing = close_prices.isna().all(axis=1)
    trailing_empty_dates = pd.DatetimeIndex([], name=selected.index.name)
    if all_close_missing.any():
        first_empty_position = int(all_close_missing.to_numpy().argmax())
        if not all_close_missing.iloc[first_empty_position:].all():
            invalid_dates = close_prices.index[all_close_missing]
            raise ValueError(
                "All-ETF missing Close dates must be a contiguous trailing block; "
                f"found non-trailing dates: {[date.date().isoformat() for date in invalid_dates]}"
            )
        trailing_empty_dates = close_prices.index[first_empty_position:]
        close_prices_for_internal_check = close_prices.iloc[:first_empty_position]
    else:
        close_prices_for_internal_check = close_prices

    for ticker in TICKERS:
        internal_missing = close_prices_for_internal_check.index[
            close_prices_for_internal_check[ticker].isna()
        ]
        if len(internal_missing):
            issues.append(
                f"{ticker}: internal Close gaps on "
                + ", ".join(date.date().isoformat() for date in internal_missing)
            )
    if issues:
        raise ValueError("ETF integrity validation failed: " + "; ".join(issues))

    return selected, ticker_level, field_level, trailing_empty_dates


def _print_missing_values(prices: pd.DataFrame, ticker_level: int) -> None:
    """Print missing-value counts for each field of each ETF."""
    print("Missing values by ETF:")
    for ticker in TICKERS:
        ticker_prices = prices.xs(ticker, axis="columns", level=ticker_level)
        missing = ticker_prices.isna().sum()
        summary = ", ".join(f"{field}={int(count)}" for field, count in missing.items())
        print(f"  {ticker}: {summary}")


def _write_atomic_csv(prices: pd.DataFrame, output_path: Path) -> None:
    """Validate a temporary round trip before atomically replacing output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            prefix=f".{output_path.stem}.",
            suffix=".tmp.csv",
            dir=output_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        prices.to_csv(temporary_path)
        reloaded = pd.read_csv(
            temporary_path,
            header=[0, 1],
            index_col=0,
            parse_dates=True,
        )
        reloaded, _, _, reloaded_trailing_dates = _validate_and_select(reloaded)

        if reloaded.empty or reloaded.shape != prices.shape:
            raise ValueError(
                "Temporary CSV round-trip shape mismatch: "
                f"expected {prices.shape}, received {reloaded.shape}."
            )
        pd.testing.assert_index_equal(reloaded.index, prices.index)
        pd.testing.assert_index_equal(reloaded.columns, prices.columns)
        pd.testing.assert_frame_equal(
            reloaded,
            prices,
            check_dtype=False,
            check_freq=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
        if len(reloaded_trailing_dates):
            print(
                "Validated shared trailing empty-price dates in temporary CSV: "
                + ", ".join(
                    date.date().isoformat() for date in reloaded_trailing_dates
                )
            )

        temporary_path.replace(output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main() -> None:
    """Download, validate, report, and save the raw ETF price data."""
    prices = yf.download(
        tickers=list(TICKERS),
        start=START_DATE,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    prices, ticker_level, _, trailing_empty_dates = _validate_and_select(prices)
    _print_missing_values(prices, ticker_level)
    if len(trailing_empty_dates):
        print(
            "Shared trailing dates with missing Close for all ETFs: "
            + ", ".join(date.date().isoformat() for date in trailing_empty_dates)
        )

    _write_atomic_csv(prices, OUTPUT_PATH)

    print(f"Start date: {prices.index.min().date().isoformat()}")
    print(f"End date:   {prices.index.max().date().isoformat()}")
    print(f"Rows:       {len(prices):,}")
    print(f"Tickers:    {', '.join(TICKERS)}")
    print(f"Saved to:   {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()
