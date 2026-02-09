"""Fetch ETF constituent holdings and weights."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import yfinance as yf

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Holding:
    symbol: str
    name: str
    weight: float  # fraction, e.g. 0.07 = 7%


def get_holdings(etf_symbol: str, top_n: int | None = None) -> list[Holding]:
    """Return the holdings of *etf_symbol* sorted by weight descending.

    Uses the yfinance fund-holdings endpoint which typically returns the
    top holdings for an ETF (often the top ~30-50 for sector ETFs and
    top ~10 for very broad ones via the free tier).

    Parameters
    ----------
    etf_symbol:
        Ticker of the ETF, e.g. ``"XLF"``.
    top_n:
        If given, limit to the *top_n* heaviest holdings.
    """
    ticker = yf.Ticker(etf_symbol)

    # yfinance exposes holdings via the `funds_data` interface
    try:
        funds = ticker.funds_data
        df = funds.top_holdings
    except Exception:
        log.warning(
            "Could not retrieve holdings via funds_data for %s, "
            "trying fallback...",
            etf_symbol,
        )
        df = None

    if df is None or df.empty:
        raise RuntimeError(
            f"No holdings data available for {etf_symbol}. "
            "Verify that this is a valid ETF ticker."
        )

    holdings: list[Holding] = []
    for symbol, row in df.iterrows():
        name = row.get("Name", row.get("holdingName", str(symbol)))
        weight = row.get("Holding Percent", row.get("holdingPercent", 0.0))
        # yfinance sometimes returns weight as a percentage (e.g. 7.5)
        # and sometimes as a fraction (e.g. 0.075). Normalise to fraction.
        if weight > 1.0:
            weight = weight / 100.0
        holdings.append(Holding(symbol=str(symbol), name=str(name), weight=float(weight)))

    holdings.sort(key=lambda h: h.weight, reverse=True)

    if top_n is not None:
        holdings = holdings[:top_n]

    return holdings
