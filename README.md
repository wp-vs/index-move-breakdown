# ETF Move Breakdown

Decompose sector-ETF (or any ETF) price moves into per-stock weighted contributions.

For a given ETF's daily move, this tool shows **how much each constituent stock contributed** to the overall index change, based on:

```
contribution_i = weight_i × stock_return_i
```

## Quick start

```bash
pip install -e .
```

### Analyse all 11 SPDR Select Sector ETFs

```bash
etf-breakdown
```

### Analyse specific ETFs

```bash
etf-breakdown XLF XLK XLE
```

### Show only top 5 holdings per ETF

```bash
etf-breakdown XLF -n 5
```

### Demo mode (no network required)

```bash
etf-breakdown --demo
```

## Web dashboard

Launch an interactive browser-based dashboard:

```bash
etf-web
```

Then open http://localhost:5000. The dashboard features:

- **Sector overview strip** — colour-coded cards showing each ETF's daily change, sorted best-to-worst
- **Sortable contributions table** — click any column header to re-sort
- **Horizontal bar chart** — waterfall-style visualisation of per-stock contributions (powered by Chart.js)
- **Data source toggle** — switch between Demo, Yahoo Finance (~15 min delay), and IB TWS (real-time)
- **ETF selector chips** — pick any combination of sector ETFs to analyse

## Price data sources

The tool supports pluggable price backends via `--source`:

| Source  | Flag              | Delay   | Requirements                            |
|---------|-------------------|---------|-----------------------------------------|
| Yahoo   | `--source yahoo`  | ~15 min | None (free, default)                    |
| IB TWS  | `--source ib`     | Real-time | TWS/Gateway running + `pip install ib_insync` |

### Using Interactive Brokers TWS

```bash
# Install the IB optional dependency
pip install -e ".[ib]"

# CLI — uses TWS on default port 7497
etf-breakdown XLF --source ib

# Custom connection
etf-breakdown XLF --source ib --ib-port 4001  # IB Gateway
etf-breakdown XLF --source ib --ib-host 192.168.1.10 --ib-port 7497

# Web dashboard — select "IB TWS" toggle in the UI
etf-web
```

IB TWS or IB Gateway must be running with the API enabled (Edit > Global Configuration > API > Settings > Enable ActiveX and Socket Clients). The default port is 7497 for TWS (paper) or 4001 for IB Gateway.

## How it works

1. **Holdings** — Fetches ETF constituent weights from Yahoo Finance via `yfinance`
2. **Prices** — Fetches current price and previous close via the selected provider (Yahoo Finance or IB TWS)
3. **Calculation** — For each stock: `contribution = portfolio_weight × (current_price / prev_close − 1)`
4. **Display** — Sorted by absolute contribution (biggest movers first), with a summary table when analysing multiple ETFs

## Output columns

| Column    | Meaning                                              |
|-----------|------------------------------------------------------|
| Weight    | Stock's weight in the ETF portfolio                  |
| Stock Chg | Individual stock's percentage change today           |
| Contrib   | This stock's weighted contribution to the ETF move   |
| Price     | Current stock price                                  |

The **Coverage** line shows what percentage of the ETF's total weight is represented by the displayed holdings. The **Explained** vs **Residual** values show how much of the ETF's move is accounted for by the visible holdings.

## Pre-defined ETFs

### SPDR Select Sector ETFs (default)
XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY

### Also recognised
SPY, QQQ, DIA, IWM — or pass any valid ETF ticker.

## Requirements

- Python >= 3.10
- `yfinance` (Yahoo Finance data)
- `rich` (terminal formatting)
- `flask` (web dashboard)
- `ib_insync` (optional — for IB TWS real-time prices)
