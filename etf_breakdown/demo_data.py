"""Sample / demo data for offline testing and demonstration.

These snapshots are representative of a typical trading day.
The weights are approximate real-world weights for these sector ETFs.
"""

from __future__ import annotations

from .engine import BreakdownResult, StockContribution

# ---------------------------------------------------------------------------
# XLF – Financials Select Sector SPDR
# ---------------------------------------------------------------------------
XLF_HOLDINGS = [
    ("BRK-B", "Berkshire Hathaway B", 0.1340),
    ("JPM",   "JPMorgan Chase",       0.1020),
    ("V",     "Visa Inc",             0.0830),
    ("MA",    "Mastercard Inc",       0.0670),
    ("BAC",   "Bank of America",      0.0460),
    ("WFC",   "Wells Fargo",          0.0360),
    ("GS",    "Goldman Sachs",        0.0310),
    ("SPGI",  "S&P Global",           0.0300),
    ("MS",    "Morgan Stanley",       0.0290),
    ("AXP",   "American Express",     0.0280),
]

XLF_PRICES = {
    "XLF":   (44.50, 44.12),
    "BRK-B": (412.30, 410.50),
    "JPM":   (198.20, 196.40),
    "V":     (281.50, 282.10),
    "MA":    (468.90, 470.20),
    "BAC":   (37.80, 37.50),
    "WFC":   (58.40, 57.90),
    "GS":    (465.20, 462.80),
    "SPGI":  (448.30, 449.10),
    "MS":    (95.70, 95.20),
    "AXP":   (222.10, 220.90),
}

# ---------------------------------------------------------------------------
# XLK – Technology Select Sector SPDR
# ---------------------------------------------------------------------------
XLK_HOLDINGS = [
    ("MSFT",  "Microsoft Corp",       0.2110),
    ("AAPL",  "Apple Inc",            0.1990),
    ("NVDA",  "NVIDIA Corp",          0.0650),
    ("AVGO",  "Broadcom Inc",         0.0530),
    ("CRM",   "Salesforce Inc",       0.0310),
    ("ADBE",  "Adobe Inc",            0.0290),
    ("AMD",   "Advanced Micro Dev",   0.0280),
    ("CSCO",  "Cisco Systems",        0.0260),
    ("ACN",   "Accenture plc",        0.0250),
    ("ORCL",  "Oracle Corp",          0.0240),
]

XLK_PRICES = {
    "XLK":   (207.80, 206.20),
    "MSFT":  (422.50, 420.80),
    "AAPL":  (191.30, 190.50),
    "NVDA":  (878.40, 872.20),
    "AVGO":  (1310.50, 1305.00),
    "CRM":   (274.80, 276.10),
    "ADBE":  (552.30, 554.00),
    "AMD":   (164.20, 162.50),
    "CSCO":  (50.40, 50.20),
    "ACN":   (338.20, 339.10),
    "ORCL":  (122.70, 121.90),
}

# ---------------------------------------------------------------------------
# XLE – Energy Select Sector SPDR
# ---------------------------------------------------------------------------
XLE_HOLDINGS = [
    ("XOM",   "Exxon Mobil",          0.2280),
    ("CVX",   "Chevron Corp",         0.1540),
    ("COP",   "ConocoPhillips",       0.0780),
    ("EOG",   "EOG Resources",        0.0530),
    ("SLB",   "Schlumberger",         0.0480),
    ("MPC",   "Marathon Petroleum",   0.0450),
    ("WMB",   "Williams Companies",   0.0420),
    ("PSX",   "Phillips 66",          0.0400),
    ("VLO",   "Valero Energy",        0.0340),
    ("OKE",   "ONEOK Inc",            0.0320),
]

XLE_PRICES = {
    "XLE":   (87.20, 86.50),
    "XOM":   (107.40, 106.80),
    "CVX":   (155.30, 154.50),
    "COP":   (114.60, 113.90),
    "EOG":   (120.80, 120.20),
    "SLB":   (52.30, 51.80),
    "MPC":   (159.40, 158.20),
    "WMB":   (38.90, 38.60),
    "PSX":   (138.70, 137.90),
    "VLO":   (145.60, 144.80),
    "OKE":   (72.40, 71.90),
}

# ---------------------------------------------------------------------------
# XLV – Health Care Select Sector SPDR
# ---------------------------------------------------------------------------
XLV_HOLDINGS = [
    ("UNH",   "UnitedHealth Group",   0.1030),
    ("LLY",   "Eli Lilly",           0.0940),
    ("JNJ",   "Johnson & Johnson",   0.0720),
    ("MRK",   "Merck & Co",          0.0570),
    ("ABBV",  "AbbVie Inc",          0.0560),
    ("TMO",   "Thermo Fisher Sci",   0.0440),
    ("ABT",   "Abbott Labs",         0.0370),
    ("PFE",   "Pfizer Inc",          0.0320),
    ("AMGN",  "Amgen Inc",           0.0310),
    ("DHR",   "Danaher Corp",        0.0290),
]

XLV_PRICES = {
    "XLV":   (141.80, 142.30),
    "UNH":   (528.40, 530.20),
    "LLY":   (782.30, 778.50),
    "JNJ":   (158.20, 158.80),
    "MRK":   (124.60, 125.10),
    "ABBV":  (172.40, 173.10),
    "TMO":   (552.80, 554.20),
    "ABT":   (108.30, 108.70),
    "PFE":   (28.60, 28.80),
    "AMGN":  (282.40, 283.10),
    "DHR":   (252.30, 253.00),
}


# ---------------------------------------------------------------------------
# Helper to generate BreakdownResult from demo data
# ---------------------------------------------------------------------------
def _build_demo_result(
    etf_sym: str,
    holdings_data: list[tuple[str, str, float]],
    prices_data: dict[str, tuple[float, float]],
) -> BreakdownResult:
    etf_curr, etf_prev = prices_data[etf_sym]
    etf_chg = (etf_curr - etf_prev) / etf_prev

    contribs = []
    for sym, name, weight in holdings_data:
        curr, prev = prices_data[sym]
        stock_ret = (curr - prev) / prev
        contribs.append(
            StockContribution(
                symbol=sym,
                name=name,
                weight=weight,
                stock_change_pct=stock_ret,
                contribution_pct=weight * stock_ret,
                stock_price=curr,
                stock_prev_close=prev,
            )
        )

    contribs.sort(key=lambda c: abs(c.contribution_pct), reverse=True)

    return BreakdownResult(
        etf_symbol=etf_sym,
        etf_price=etf_curr,
        etf_prev_close=etf_prev,
        etf_change_pct=etf_chg,
        contributions=contribs,
    )


DEMO_ETFS: dict[str, tuple[list, dict]] = {
    "XLF": (XLF_HOLDINGS, XLF_PRICES),
    "XLK": (XLK_HOLDINGS, XLK_PRICES),
    "XLE": (XLE_HOLDINGS, XLE_PRICES),
    "XLV": (XLV_HOLDINGS, XLV_PRICES),
}


def get_demo_results(etf_symbols: list[str] | None = None) -> list[BreakdownResult]:
    """Return demo BreakdownResults for the requested ETFs."""
    if etf_symbols is None:
        etf_symbols = list(DEMO_ETFS.keys())

    results = []
    for sym in etf_symbols:
        data = DEMO_ETFS.get(sym.upper())
        if data is None:
            continue
        holdings_data, prices_data = data
        results.append(_build_demo_result(sym.upper(), holdings_data, prices_data))
    return results
