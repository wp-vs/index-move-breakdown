"""Flask web server exposing the ETF breakdown as a JSON API + dashboard."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .demo_data import DEMO_ETFS, get_demo_results
from .engine import BreakdownResult, compute_breakdown
from .holdings import get_holdings
from .prices import get_prices, available_providers
from .sectors import ALL_KNOWN_ETFS, SECTOR_ETFS

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result_to_dict(r: BreakdownResult) -> dict:
    """Serialise a BreakdownResult to a JSON-friendly dict."""
    return {
        "etf_symbol": r.etf_symbol,
        "etf_name": ALL_KNOWN_ETFS.get(r.etf_symbol, r.etf_symbol),
        "etf_price": r.etf_price,
        "etf_prev_close": r.etf_prev_close,
        "etf_change_pct": round(r.etf_change_pct * 100, 4),
        "explained_pct": round(r.explained_pct * 100, 4),
        "unexplained_pct": round(r.unexplained_pct * 100, 4),
        "coverage_pct": round(
            sum(c.weight for c in r.contributions) * 100, 2
        ),
        "contributions": [
            {
                "symbol": c.symbol,
                "name": c.name,
                "weight": round(c.weight * 100, 3),
                "stock_change_pct": round(c.stock_change_pct * 100, 4),
                "contribution_pct": round(c.contribution_pct * 100, 4),
                "stock_price": c.stock_price,
                "stock_prev_close": c.stock_prev_close,
            }
            for c in r.contributions
        ],
    }


def _analyse_live(etf_symbol: str, top_n: int | None, source: str = "yahoo") -> dict | None:
    """Run the live pipeline for one ETF using the specified price source."""
    try:
        holdings = get_holdings(etf_symbol, top_n=top_n)
    except RuntimeError:
        return None

    if not holdings:
        return None

    all_symbols = [h.symbol for h in holdings] + [etf_symbol]
    prices = get_prices(all_symbols, source=source)

    etf_snap = prices.get(etf_symbol)
    if etf_snap is None:
        return None

    result = compute_breakdown(etf_symbol, holdings, prices, etf_snap)
    return _result_to_dict(result)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/sectors")
def api_sectors():
    """Return the list of known sector ETFs."""
    return jsonify(
        {"sector_etfs": SECTOR_ETFS, "broad_etfs": ALL_KNOWN_ETFS}
    )


@app.route("/api/providers")
def api_providers():
    """Return available price data sources."""
    return jsonify({"providers": available_providers()})


@app.route("/api/breakdown")
def api_breakdown():
    """Analyse one or more ETFs and return the breakdown as JSON.

    Query params:
        etfs:    comma-separated list of ETF tickers (default: all SPDR sectors)
        top:     max holdings per ETF (optional)
        demo:    if "1", use sample data
        source:  price provider — "yahoo" (default) or "ib"
    """
    raw = request.args.get("etfs", "")
    etf_symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
    if not etf_symbols:
        etf_symbols = list(SECTOR_ETFS.keys())

    top_n_str = request.args.get("top", "")
    top_n = int(top_n_str) if top_n_str.isdigit() else None

    use_demo = request.args.get("demo", "0") == "1"
    source = request.args.get("source", "yahoo")

    results = []
    if use_demo:
        for r in get_demo_results(etf_symbols):
            d = _result_to_dict(r)
            if top_n is not None:
                d["contributions"] = d["contributions"][:top_n]
            results.append(d)
    else:
        for sym in etf_symbols:
            d = _analyse_live(sym, top_n=top_n, source=source)
            if d is not None:
                results.append(d)

    return jsonify({"results": results, "source": source})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="etf-web",
        description="Launch the ETF breakdown web dashboard",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=5000, help="Port (default 5000)"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host (default 0.0.0.0)"
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Start in demo mode (pre-select demo data)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Debug logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    print(f"Starting ETF Breakdown dashboard on http://{args.host}:{args.port}")
    print(f"Available price sources: {', '.join(available_providers())}")
    print("Press Ctrl+C to stop.")
    app.run(host=args.host, port=args.port, debug=args.verbose)


if __name__ == "__main__":
    main()
