"""Price provider abstraction and registry.

Defines the ``PriceProvider`` protocol so that different backends
(Yahoo Finance, Interactive Brokers, etc.) can be swapped in without
changing the rest of the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    """A single symbol's price snapshot."""

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


class PriceProvider(Protocol):
    """Interface that every price backend must implement."""

    name: str

    def get_prices(self, symbols: list[str]) -> dict[str, PriceSnapshot]:
        """Return a mapping of symbol -> PriceSnapshot."""
        ...

    def close(self) -> None:
        """Clean up any resources (connections, etc.)."""
        ...


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type] = {}


def register_provider(name: str, cls: type) -> None:
    _PROVIDERS[name] = cls


def get_provider(name: str, **kwargs) -> PriceProvider:
    """Instantiate a provider by name.

    Raises ``ValueError`` if the name is unknown or dependencies are missing.
    """
    if name not in _PROVIDERS:
        available = ", ".join(sorted(_PROVIDERS)) or "(none)"
        raise ValueError(
            f"Unknown price source {name!r}. Available: {available}"
        )
    return _PROVIDERS[name](**kwargs)


def available_providers() -> list[str]:
    return sorted(_PROVIDERS)
