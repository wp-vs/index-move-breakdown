"""Rich-based terminal display for ETF move breakdowns."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.text import Text

from .engine import BreakdownResult

console = Console(width=120)


def _colour(value: float) -> str:
    """Return a rich colour tag name for positive/negative values."""
    if value > 0:
        return "green"
    if value < 0:
        return "red"
    return "white"


def _fmt_pct(value: float) -> Text:
    """Format a fraction as a signed percentage string with colour."""
    pct = value * 100
    sign = "+" if pct >= 0 else ""
    txt = f"{sign}{pct:.3f}%"
    return Text(txt, style=_colour(value))


def _fmt_price(value: float) -> str:
    return f"${value:,.2f}"


def print_breakdown(result: BreakdownResult) -> None:
    """Print a single ETF's move breakdown as a rich table."""
    etf_pct = result.etf_change_pct * 100
    sign = "+" if etf_pct >= 0 else ""
    colour = _colour(result.etf_change_pct)

    header = (
        f"[bold]{result.etf_symbol}[/bold]  "
        f"{_fmt_price(result.etf_prev_close)} -> {_fmt_price(result.etf_price)}  "
        f"[{colour}]{sign}{etf_pct:.2f}%[/{colour}]"
    )
    console.print()
    console.rule(header)

    table = Table(
        show_header=True,
        header_style="bold cyan",
        show_lines=False,
        pad_edge=True,
        expand=False,
    )
    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column("Ticker", style="bold", min_width=5, max_width=6)
    table.add_column("Name", min_width=18, max_width=24, no_wrap=True)
    table.add_column("Weight", justify="right", min_width=6)
    table.add_column("Stock Chg", justify="right", min_width=9)
    table.add_column("Contrib", justify="right", min_width=9)
    table.add_column("Price", justify="right", min_width=9)

    for i, c in enumerate(result.contributions, 1):
        table.add_row(
            str(i),
            c.symbol,
            c.name[:24],
            f"{c.weight * 100:.2f}%",
            _fmt_pct(c.stock_change_pct),
            _fmt_pct(c.contribution_pct),
            _fmt_price(c.stock_price),
        )

    console.print(table)

    # Summary row
    explained = result.explained_pct * 100
    unexplained = result.unexplained_pct * 100
    total_weight = sum(c.weight for c in result.contributions) * 100
    console.print(
        f"  [dim]Coverage: [bold]{total_weight:.1f}%[/bold] of ETF  |  "
        f"Explained: [{_colour(result.explained_pct)}]{explained:+.3f}%[/{_colour(result.explained_pct)}]  |  "
        f"Residual: {unexplained:+.3f}%[/dim]"
    )


def print_summary_table(results: list[BreakdownResult]) -> None:
    """Print a compact summary comparing multiple ETFs side-by-side."""
    if not results:
        return

    console.print()
    console.rule("[bold]Sector Overview[/bold]")

    table = Table(
        show_header=True,
        header_style="bold cyan",
        expand=False,
    )
    table.add_column("ETF", style="bold", width=5)
    table.add_column("Change", justify="right", min_width=9)
    table.add_column("Top +", min_width=5, max_width=6)
    table.add_column("Contrib", justify="right", min_width=9)
    table.add_column("Top -", min_width=5, max_width=6)
    table.add_column("Contrib", justify="right", min_width=9)

    for r in sorted(results, key=lambda r: r.etf_change_pct, reverse=True):
        positives = [c for c in r.contributions if c.contribution_pct > 0]
        negatives = [c for c in r.contributions if c.contribution_pct < 0]

        top_pos = max(positives, key=lambda c: c.contribution_pct) if positives else None
        top_neg = min(negatives, key=lambda c: c.contribution_pct) if negatives else None

        table.add_row(
            r.etf_symbol,
            _fmt_pct(r.etf_change_pct),
            top_pos.symbol if top_pos else "-",
            _fmt_pct(top_pos.contribution_pct) if top_pos else Text("-"),
            top_neg.symbol if top_neg else "-",
            _fmt_pct(top_neg.contribution_pct) if top_neg else Text("-"),
        )

    console.print(table)
    console.print()
