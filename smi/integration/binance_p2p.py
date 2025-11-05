import asyncio
import logging

import httpx

from config.app import log_execution_time
from config.config import settings
from smi.parser import process_market_data, fetch_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)

WINDOW_CONFIG = {
    "USDTAZN": {'BUY': {'start': 1, 'end': 10, 'min_amount': 0, 'verify': True, 'bank': ['Kapitalbank']},
                'SELL': {'start': 1, 'end': 10, 'min_amount': 0, 'verify': True, 'bank': ['Kapitalbank']}},
}
DEFAULT_WINDOW = {'start': 1, 'end': 5, 'min_amount': 0, 'verify': True, 'bank': []}

@log_execution_time
async def fetch_binance_p2p_symbols(stock_market: StockMarket) -> list[Symbol]:
    tokens = ["USDT"]  # , "USDC"
    fiats = ["KZT", "TJS", "AZN", "ARS"]
    symbols = [Symbol(asset_left=t, asset_right=f) for t in tokens for f in fiats]
    stock_market.symbols = []
    stock_market.symbols = symbols
    return symbols

@log_execution_time
async def fetch_binance_p2p_rates(market: StockMarket) -> list[SMCourse]:
    coros = [compute_pair_avg(market, symbol) for symbol in market.symbols]
    results = await asyncio.gather(*coros, return_exceptions=True)
    filtered: list[dict] = []
    for res in results:
        if isinstance(res, Exception):
            logger.warning(f"Error fetching {market.name} P2P data: {res}")
            continue
        filtered.append(res)
    return await process_market_data(
        market,
        filtered,
        extract_symbol=lambda item: item['symbol'],
        extract_price=lambda item: item['price'],
        p2p=True
    )

HEADERS = {
    "User-Agent": "stockmarketinfo/1.0",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

async def fetch_ads(market: StockMarket, symbol: Symbol, side: str, rows: int = 20, min_amount: float = .0, verify: bool = True, bank: list = None) -> list[float]:
    payload = {
        "asset": symbol.asset_left.asset,
        "fiat": symbol.asset_right.asset,
        "tradeType": side,
        "page": 1,
        "rows": rows,
        "merchantCheck": verify,
        "proMerchantAds": False,
        "transAmount": str(min_amount),
    }
    if bank:
        payload['payTypes'] = bank
    data = await fetch_data(market.rates_url.unicode_string(), json=payload, headers=HEADERS, method="POST")
    items = data.get("data", [])
    prices = []
    for adv_wrapper in items:
        try:
            price = float(adv_wrapper["adv"]["price"])
            prices.append(price)
        except (KeyError, TypeError, ValueError):
            continue
    match side:
        case "BUY":
            return sorted(prices)[:rows]
        case "SELL":
            return sorted(prices, reverse=True)[:rows]
        case _:
            return []


async def compute_pair_avg(market: StockMarket, symbol: Symbol) -> dict[str, tuple[float, float]]:
    window = WINDOW_CONFIG.get(symbol.symbol, {'BUY': DEFAULT_WINDOW, 'SELL': DEFAULT_WINDOW})
    buy_list, sell_list = await asyncio.gather(
        fetch_ads(market, symbol, "BUY", min_amount=window['BUY']['min_amount'], verify=window['BUY']['verify'], bank=window['BUY']['bank']),
        fetch_ads(market, symbol, "SELL", min_amount=window['SELL']['min_amount'], verify=window['SELL']['verify'], bank=window['SELL']['bank'])
    )

    def avg(prices: list[float], start: int, end: int) -> float:
        sub = prices[start-1:end]
        return sum(sub) / len(sub) if sub else .0
    return {"symbol": symbol.symbol, "price": (avg(buy_list, window['BUY']['start'], window['BUY']['end']),
                                               avg(sell_list, window['SELL']['start'], window['SELL']['end']))}

