"""Core calculation: decompose an ETF move into per-stock contributions."""

from __future__ import annotations

from dataclasses import dataclass

from .holdings import Holding
from .prices import PriceSnapshot


@dataclass(frozen=True, slots=True)
class StockContribution:
    """One stock's contribution to the ETF move."""

    symbol: str
    name: str
    weight: float  # portfolio weight as fraction (e.g. 0.07)
    stock_change_pct: float  # individual stock return (fraction)
    contribution_pct: float  # weight × stock_return  (fraction)
    stock_price: float
    stock_prev_close: float


@dataclass(frozen=True, slots=True)
class BreakdownResult:
    """Full breakdown for one ETF."""

    etf_symbol: str
    etf_price: float
    etf_prev_close: float
    etf_change_pct: float  # fraction
    contributions: list[StockContribution]

    @property
    def explained_pct(self) -> float:
        """Sum of all constituent contributions (fraction)."""
        return sum(c.contribution_pct for c in self.contributions)

    @property
    def unexplained_pct(self) -> float:
        """Portion of the ETF move not explained by the visible holdings."""
        return self.etf_change_pct - self.explained_pct


def compute_breakdown(
    etf_symbol: str,
    holdings: list[Holding],
    prices: dict[str, PriceSnapshot],
    etf_price: PriceSnapshot,
) -> BreakdownResult:
    """Compute the contribution of each holding to the ETF move.

    The core formula per stock is::

        contribution_i = weight_i × (price_i / prev_close_i − 1)

    Summing all contributions gives an approximation of the ETF's
    percentage move (exact up to rebalancing, dividends, fees, and
    any holdings we don't have data for).
    """
    contributions: list[StockContribution] = []

    for h in holdings:
        snap = prices.get(h.symbol)
        if snap is None:
            continue

        stock_return = snap.change_pct
        contribution = h.weight * stock_return

        contributions.append(
            StockContribution(
                symbol=h.symbol,
                name=h.name,
                weight=h.weight,
                stock_change_pct=stock_return,
                contribution_pct=contribution,
                stock_price=snap.current_price,
                stock_prev_close=snap.previous_close,
                )
        )

    # Sort by absolute contribution descending — biggest movers first
    contributions.sort(key=lambda c: abs(c.contribution_pct), reverse=True)

    return BreakdownResult(
        etf_symbol=etf_symbol,
        etf_price=etf_price.current_price,
        etf_prev_close=etf_price.previous_close,
        etf_change_pct=etf_price.change_pct,
        contributions=contributions,
    )
