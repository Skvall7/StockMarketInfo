"""Интеграция Bybit P2P.

Пары задаются вручную, потому что P2P не является обычным spot-источником.
Для каждой пары считаются средние BUY/SELL по `WINDOW_CONFIG` или `DEFAULT_WINDOW`,
затем результат передается в `process_market_data(..., p2p=True)`.
"""

import logging
import asyncio

from typing import Optional

from config.app import log_execution_time
from config.config import settings
from smi.parser import fetch_data, process_market_data
from smi.schemas import Symbol, StockMarket, SMCourse

logger = logging.getLogger(settings.title)

# Параметры окон усреднения: можно добавить индивидуальные
WINDOW_CONFIG = {
    "USDTRUB": {'BUY': {'start': 3, 'end': 5, 'min_amount': 0, 'verify': True}, 'SELL': {'start': 3, 'end': 5, 'min_amount': 0, 'verify': True}},
    "USDTAZN": {'BUY': {'start': 1, 'end': 10, 'min_amount': 2000, 'verify': True}, 'SELL': {'start': 1, 'end': 10, 'min_amount': 2000, 'verify': True}},
}
DEFAULT_WINDOW = {'start': 2, 'end': 4, 'min_amount': 0, 'verify': True}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.bybit.com"
}

@log_execution_time
async def fetch_bybit_p2p_symbols(stock_market: StockMarket) -> list[Symbol]:
    """Создает поддерживаемые P2P-пары Bybit и сохраняет прямые/обратные символы."""
    # Нужно найти решение как получать список токенов и фиаты
    tokens = ["USDT"]   # , "USDC"
    fiats = ["RUB", "KZT", "AZN", "TJS", "ARS"]
    symbols = [Symbol(asset_left=t, asset_right=f) for t in tokens for f in fiats]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

async def fetch_ads(market: StockMarket, symbol: Symbol, side: str, rows: int = 50, min_amount: Optional[float] = .0,
                    merchant_only: bool = True,) -> list[float]:
    """Возвращает отсортированные цены объявлений Bybit P2P для одной стороны сделки."""
    # TODO требуется до адоптировать p2p, в частности запросы
    prices: list[float] = []
    payload = {"tokenId": symbol.asset_left.asset, "currencyId": symbol.asset_right.asset, "side": side, "page": '1', "size": str(rows)}
    if min_amount > 0:
        payload["amount"] = str(min_amount)
    data = await fetch_data(market.rates_url.unicode_string(), json=payload, headers=HEADERS, method="POST")
    items = data.get("result", {}).get("items", []) or []
    for item in items:
        if merchant_only:
            if "VA" not in item.get("authTag", []):
                continue
        try:
            prices.append(float(item["price"]))
        except (KeyError, ValueError):
            continue
    return sorted(prices) if side == "1" else sorted(prices, reverse=True)

async def compute_pair_avg(market: StockMarket, symbol: Symbol ) -> dict[str, tuple[float, float]]:
    """Считает средние BUY/SELL по окну пары или родительскому `DEFAULT_WINDOW`."""
    window = WINDOW_CONFIG.get(symbol.symbol, {'BUY': DEFAULT_WINDOW, 'SELL': DEFAULT_WINDOW})
    buy_list, sell_list = await asyncio.gather(fetch_ads(market, symbol, "1", min_amount=window['BUY']['min_amount'], merchant_only=window['BUY']['verify']),
                                               fetch_ads(market, symbol, "0", min_amount=window['SELL']['min_amount'], merchant_only=window['SELL']['verify']))

    def avg(prices: list[float], start: int, end: int) -> float:
        sub = prices[start-1:end]
        return sum(sub) / len(sub) if sub else .0
    return {"symbol": symbol.symbol, "price": (avg(buy_list, window['BUY']['start'], window['BUY']['end']), avg(sell_list, window['SELL']['start'], window['SELL']['end']))}


@log_execution_time
async def fetch_bybit_p2p_rates(market: StockMarket) -> list[SMCourse]:
    """Параллельно считает средние P2P-цены и возвращает `list[SMCourse]`."""
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
        filtered,   # results,
        extract_symbol=lambda item: item['symbol'],
        extract_price=lambda item: item['price'],
        p2p=True
    )
