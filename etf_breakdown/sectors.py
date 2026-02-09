"""Pre-defined sector ETF universe."""

# SPDR Select Sector ETFs (S&P 500 sectors)
SECTOR_ETFS: dict[str, str] = {
    "XLB": "Materials",
    "XLC": "Communication Services",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLI": "Industrials",
    "XLK": "Technology",
    "XLP": "Consumer Staples",
    "XLRE": "Real Estate",
    "XLU": "Utilities",
    "XLV": "Health Care",
    "XLY": "Consumer Discretionary",
}

# Broader / popular ETFs people may want to decompose
BROAD_ETFS: dict[str, str] = {
    "SPY": "S&P 500",
    "QQQ": "Nasdaq-100",
    "DIA": "Dow Jones Industrial Average",
    "IWM": "Russell 2000",
}

ALL_KNOWN_ETFS: dict[str, str] = {**SECTOR_ETFS, **BROAD_ETFS}
