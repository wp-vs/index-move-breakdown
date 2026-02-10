"""Yahoo Finance price provider (via yfinance)."""

from __future__ import annotations

import logging

import yfinance as yf

from . import PriceSnapshot, register_provider

log = logging.getLogger(__name__)


class YahooProvider:
    """Fetch prices from Yahoo Finance (~15 min delayed, free)."""

    name = "yahoo"

    def get_prices(self, symbols: list[str]) -> dict[str, PriceSnapshot]:
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
                log.warning("Yahoo: could not fetch price for %s", sym)

        return snapshots

    def close(self) -> None:
        pass


register_provider("yahoo", YahooProvider)
