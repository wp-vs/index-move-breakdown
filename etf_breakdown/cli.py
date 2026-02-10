"""CLI entry-point for ETF move breakdown analysis."""

from __future__ import annotations

import argparse
import logging
import sys

from .display import console, print_breakdown, print_summary_table
from .engine import BreakdownResult, compute_breakdown
from .holdings import get_holdings
from .prices import get_prices, available_providers
from .sectors import ALL_KNOWN_ETFS, SECTOR_ETFS

log = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    providers = available_providers()
    p = argparse.ArgumentParser(
        prog="etf-breakdown",
        description=(
            "Decompose sector-ETF moves into per-stock contributions.\n\n"
            "With no arguments, analyses all 11 SPDR Select Sector ETFs.\n"
            "Pass one or more tickers to analyse specific ETFs."
        ),
    )
    p.add_argument(
        "etfs",
        nargs="*",
        metavar="ETF",
        help="ETF ticker(s) to analyse (default: all SPDR sectors)",
    )
    p.add_argument(
        "-n",
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Only show top N holdings per ETF (default: all available)",
    )
    p.add_argument(
        "-s",
        "--source",
        default="yahoo",
        choices=providers,
        help=f"Price data source (default: yahoo). Available: {', '.join(providers)}",
    )
    p.add_argument(
        "--ib-host",
        default="127.0.0.1",
        help="IB TWS/Gateway host (default: 127.0.0.1)",
    )
    p.add_argument(
        "--ib-port",
        type=int,
        default=7497,
        help="IB TWS/Gateway port (default: 7497 for TWS, use 4001 for Gateway)",
    )
    p.add_argument(
        "--ib-client-id",
        type=int,
        default=10,
        help="IB API client ID (default: 10)",
    )
    p.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip the cross-sector summary table",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Use built-in sample data (no network required)",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return p


def _resolve_etfs(args_etfs: list[str]) -> list[str]:
    """Return a list of ETF symbols to process."""
    if not args_etfs:
        return list(SECTOR_ETFS.keys())
    return [e.upper() for e in args_etfs]


def _provider_kwargs(args) -> dict:
    """Build kwargs for the price provider from CLI args."""
    if args.source == "ib":
        return {
            "host": args.ib_host,
            "port": args.ib_port,
            "client_id": args.ib_client_id,
        }
    return {}


def _analyse_etf(
    etf_symbol: str,
    top_n: int | None,
    source: str,
    provider_kwargs: dict,
) -> BreakdownResult | None:
    """Run the full pipeline for a single ETF. Returns None on failure."""
    label = ALL_KNOWN_ETFS.get(etf_symbol, etf_symbol)
    console.print(f"[dim]Fetching holdings for {etf_symbol} ({label})...[/dim]")

    try:
        holdings = get_holdings(etf_symbol, top_n=top_n)
    except RuntimeError as exc:
        console.print(f"[red]  {exc}[/red]")
        return None

    if not holdings:
        console.print(f"[yellow]  No holdings returned for {etf_symbol}[/yellow]")
        return None

    all_symbols = [h.symbol for h in holdings] + [etf_symbol]
    source_label = "IB TWS" if source == "ib" else "Yahoo Finance"
    console.print(
        f"[dim]  Fetching prices for {len(holdings)} holdings via {source_label}...[/dim]"
    )
    prices = get_prices(all_symbols, source=source, **provider_kwargs)

    etf_snap = prices.get(etf_symbol)
    if etf_snap is None:
        console.print(f"[red]  Could not fetch price for ETF {etf_symbol}[/red]")
        return None

    return compute_breakdown(etf_symbol, holdings, prices, etf_snap)


def _run_demo(etf_symbols: list[str], top_n: int | None) -> list[BreakdownResult]:
    """Run with built-in sample data — no network access needed."""
    from .demo_data import DEMO_ETFS, get_demo_results

    available = list(DEMO_ETFS.keys())
    requested = [s for s in etf_symbols if s in DEMO_ETFS]

    if not requested:
        console.print(
            f"[yellow]Demo data available for: {', '.join(available)}. "
            f"None of the requested ETFs matched.[/yellow]"
        )
        requested = available

    console.print(f"[bold cyan]-- DEMO MODE (sample data) --[/bold cyan]")
    results = get_demo_results(requested)

    if top_n is not None:
        trimmed = []
        for r in results:
            trimmed.append(
                BreakdownResult(
                    etf_symbol=r.etf_symbol,
                    etf_price=r.etf_price,
                    etf_prev_close=r.etf_prev_close,
                    etf_change_pct=r.etf_change_pct,
                    contributions=r.contributions[:top_n],
                )
            )
        results = trimmed

    return results


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    etf_symbols = _resolve_etfs(args.etfs)

    if args.demo:
        results = _run_demo(etf_symbols, top_n=args.top)
    else:
        pkw = _provider_kwargs(args)
        results = []
        for sym in etf_symbols:
            result = _analyse_etf(sym, top_n=args.top, source=args.source,
                                  provider_kwargs=pkw)
            if result is not None:
                results.append(result)

    for r in results:
        print_breakdown(r)

    if len(results) > 1 and not args.no_summary:
        print_summary_table(results)

    if not results:
        console.print("[red]No ETFs could be analysed.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
