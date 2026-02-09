"""Fetch near-real-time and previous-close prices for a batch of tickers."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import yfinance as yf

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    symbol: str
    current_price: float
    previous_close: float

    @property
    def change(self) -> float:
        return self.current_price - self.previous_close

    @property
    def change_pct(self) -> float:
        if self.previous_close == 0:
            return 0.0
        return (self.current_price - self.previous_close) / self.previous_close


def get_prices(symbols: list[str]) -> dict[str, PriceSnapshot]:
    """Fetch current price and previous close for every symbol in *symbols*.

    Uses ``yfinance.download`` with ``period="1d"`` for the batch, plus
    ``Ticker.fast_info`` for the real-time quote, which gives the
    closest-to-live price available through the free Yahoo Finance API
    (typically delayed ~15 min during market hours).
    """
    snapshots: dict[str, PriceSnapshot] = {}

    tickers = yf.Tickers(" ".join(symbols))

    for sym in symbols:
        try:
            ticker = tickers.tickers[sym]
            info = ticker.fast_info
            current = float(info.last_price)
            prev_close = float(info.previous_close)
            snapshots[sym] = PriceSnapshot(
                symbol=sym,
                current_price=current,
                previous_close=prev_close,
            )
        except Exception:
            log.warning("Could not fetch price for %s — skipping", sym)

    return snapshots
