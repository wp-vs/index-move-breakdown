"""Interactive Brokers TWS/Gateway price provider (via ib_insync).

Provides real-time streaming prices with no delay.  Requires:
  - IB TWS or IB Gateway running locally
  - ``pip install ib_insync``
  - Market data subscriptions for US equities

Default connection: 127.0.0.1:7497 (TWS paper) / 4001 (Gateway).
"""

from __future__ import annotations

import logging
import time

from . import PriceSnapshot, register_provider

log = logging.getLogger(__name__)

# Guard the import so the rest of the package works without ib_insync
try:
    from ib_insync import IB, Contract, Stock, MarketOrder, util
    _IB_AVAILABLE = True
except ImportError:
    _IB_AVAILABLE = False


class IBProvider:
    """Fetch real-time prices from Interactive Brokers TWS / Gateway."""

    name = "ib"

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,
        client_id: int = 10,
        timeout: float = 10.0,
    ):
        if not _IB_AVAILABLE:
            raise ImportError(
                "ib_insync is required for the IB provider.  "
                "Install it with:  pip install ib_insync"
            )

        self._host = host
        self._port = port
        self._client_id = client_id
        self._timeout = timeout
        self._ib: IB | None = None

    def _connect(self) -> IB:
        """Lazily connect to TWS/Gateway on first use."""
        if self._ib is not None and self._ib.isConnected():
            return self._ib

        self._ib = IB()
        log.info("Connecting to IB on %s:%s (clientId=%s)...",
                 self._host, self._port, self._client_id)
        self._ib.connect(
            self._host, self._port,
            clientId=self._client_id,
            timeout=self._timeout,
        )
        log.info("Connected to IB — server version %s", self._ib.client.serverVersion())
        return self._ib

    def get_prices(self, symbols: list[str]) -> dict[str, PriceSnapshot]:
        ib = self._connect()

        # Build US stock contracts for each symbol
        contracts = []
        sym_map: dict[int, str] = {}  # conId -> original symbol
        for sym in symbols:
            # IB uses different symbol format for BRK.B etc.
            ib_sym = sym.replace("-", " ")
            c = Stock(ib_sym, "SMART", "USD")
            contracts.append(c)

        # Qualify contracts (resolve to full contract details)
        qualified = ib.qualifyContracts(*contracts)
        valid_contracts = []
        valid_symbols = []
        for c, sym in zip(qualified, symbols):
            if c.conId:
                valid_contracts.append(c)
                valid_symbols.append(sym)
            else:
                log.warning("IB: could not qualify contract for %s", sym)

        if not valid_contracts:
            return {}

        # Request snapshot market data for all contracts
        # Using snapshot=True gets a single point-in-time quote
        tickers = []
        for c in valid_contracts:
            t = ib.reqMktData(c, snapshot=True)
            tickers.append(t)

        # Wait for data to arrive (snapshots resolve quickly)
        deadline = time.time() + self._timeout
        while time.time() < deadline:
            ib.sleep(0.1)
            # Check if all tickers have resolved
            if all(_ticker_ready(t) for t in tickers):
                break

        snapshots: dict[str, PriceSnapshot] = {}
        for sym, t in zip(valid_symbols, tickers):
            try:
                current = _best_price(t)
                prev_close = float(t.close) if _is_valid(t.close) else None

                if current is None or prev_close is None:
                    log.warning("IB: incomplete data for %s (last=%s, close=%s)",
                                sym, t.last, t.close)
                    continue

                snapshots[sym] = PriceSnapshot(
                    symbol=sym,
                    current_price=current,
                    previous_close=prev_close,
                )
            except Exception:
                log.warning("IB: error processing ticker for %s", sym, exc_info=True)

        # Cancel market data subscriptions
        for t in tickers:
            ib.cancelMktData(t.contract)

        return snapshots

    def close(self) -> None:
        """Disconnect from TWS/Gateway."""
        if self._ib is not None and self._ib.isConnected():
            self._ib.disconnect()
            log.info("Disconnected from IB")
        self._ib = None


def _is_valid(value) -> bool:
    """Check if an IB ticker value is a real number (not nan/None/unset)."""
    if value is None:
        return False
    try:
        f = float(value)
        return f == f and f > 0  # filters nan and zero/negative
    except (TypeError, ValueError):
        return False


def _best_price(t) -> float | None:
    """Pick the best available price from an IB ticker snapshot.

    Preference order: last trade > mid(bid,ask) > close.
    """
    if _is_valid(t.last):
        return float(t.last)
    if _is_valid(t.bid) and _is_valid(t.ask):
        return (float(t.bid) + float(t.ask)) / 2.0
    if _is_valid(t.close):
        return float(t.close)
    return None


def _ticker_ready(t) -> bool:
    """Check whether a snapshot ticker has received data."""
    return _is_valid(t.last) or (_is_valid(t.bid) and _is_valid(t.ask)) or _is_valid(t.close)


# Only register if ib_insync is installed
if _IB_AVAILABLE:
    register_provider("ib", IBProvider)
