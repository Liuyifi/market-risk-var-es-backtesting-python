# Data Provenance and Environment

## Market data snapshot

- **Data source:** Yahoo Finance accessed through `yfinance`.
- **Tickers:** SPY, QQQ, TLT, and GLD.
- **Frequency:** Daily.
- **Download start parameter:** `2018-01-01`.
- **Price adjustment:** `auto_adjust=True`.
- **Raw CSV date range:** 2018-01-02 through 2026-09-22.
- **Latest valid OHLC date:** 2026-09-21.
- **Invalid trailing date:** On 2026-09-22, Open, High, Low, and Close are missing for all four ETFs, so the row is not a valid price observation. Contrary to the audit note that described zero volume, the frozen raw CSV contains non-zero Volume values on that row: GLD 6,466,737; QQQ 39,451,977; SPY 34,483,102; and TLT 22,666,158. Volume is not used as evidence that valid prices exist.
- **Documented retrieval date:** 2026-09-23.

The data files are a frozen project snapshot. A future download may differ because of additional trading days, vendor revisions, corporate-action adjustments, or changes to the Yahoo Finance or `yfinance` interface. The download script supports future updates, but the current notebooks and reported results correspond to this frozen snapshot.

## Snapshot checksums (SHA-256)

| File | SHA-256 |
|---|---|
| `data/raw/etf_prices.csv` | `861a855fc44cdcc31ad96485f35b9c8cae20af2592deb0022c207ff3a6141b18` |
| `data/processed/asset_returns.csv` | `f361d0fe126a9e6f6fa11babcdcccb9470646dd1cc7d842265076af72a56d22e` |
| `data/processed/portfolio_returns.csv` | `1f77fd8238eaa327a86421585abce794b1a338135b0f46919492d02078b8820d` |

## Reproducibility environment

| Component | Version |
|---|---:|
| Python | 3.9.6 |
| pandas | 2.3.3 |
| NumPy | 2.0.2 |
| SciPy | 1.13.1 |
| Matplotlib | 3.9.4 |
| Seaborn | 0.13.2 |
| yfinance | 1.2.0 |
| Jupyter | 1.1.1 |

Versions were read from the project root virtual environment on 2026-09-23. The directly used Python packages are pinned in `requirements.txt`; transitive packages remain managed by `pip` dependency resolution.
