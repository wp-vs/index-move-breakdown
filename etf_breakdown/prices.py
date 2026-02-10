"""Price fetching — delegates to the configured provider backend.

Import providers on module load so they self-register.
"""

from __future__ import annotations

# Re-export PriceSnapshot from the provider package so existing
# imports (``from .prices import PriceSnapshot``) continue to work.
from .providers import PriceSnapshot, get_provider, available_providers  # noqa: F401

# Import provider modules so they register themselves on startup.
from .providers import yahoo as _yahoo  # noqa: F401

try:
    from .providers import ib as _ib  # noqa: F401
except Exception:
    pass  # ib_insync not installed — that's fine


def get_prices(
    symbols: list[str],
    source: str = "yahoo",
    **provider_kwargs,
) -> dict[str, PriceSnapshot]:
    """Fetch prices using the named provider.

    Parameters
    ----------
    symbols:
        List of ticker symbols to fetch.
    source:
        Provider name — ``"yahoo"`` (default) or ``"ib"``.
    **provider_kwargs:
        Extra kwargs forwarded to the provider constructor
        (e.g. ``host``, ``port``, ``client_id`` for IB).
    """
    provider = get_provider(source, **provider_kwargs)
    try:
        return provider.get_prices(symbols)
    finally:
        provider.close()
