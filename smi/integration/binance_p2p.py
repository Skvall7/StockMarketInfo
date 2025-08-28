import asyncio
import logging

import httpx

from config.app import log_execution_time
from config.config import settings
from smi.parser import process_market_data, fetch_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_binance_p2p_symbols(stock_market: StockMarket) -> list[Symbol]:
    symbols = [Symbol(asset_left='USDT', asset_right='AZN')]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

@log_execution_time
async def fetch_binance_p2p_rates(market: StockMarket) -> list[SMCourse]:
    async with httpx.AsyncClient() as client:
        coros = [compute_pair_avg_binance(client, market, symbol) for symbol in market.symbols]
        results = await asyncio.gather(*coros, return_exceptions=True)
    print(results)
    return await process_market_data(
        market,
        results,
        extract_symbol=lambda item: item['symbol'],
        extract_price=lambda item: item['price'],
        p2p=True
    )

logger = logging.getLogger(settings.title)

# Пары токен/фиат
TOKENS = ["USDT", "USDC"]
FIATS = ["RUB", "UZS", "KZT", "TJS", "AZN"]

# Окна усреднения (по умолчанию — 1–5 объявлений)
WINDOW_CONFIG = {
    "USDTRUB": {"BUY": (1, 5), "SELL": (1, 5)},
    # можно добавить кастомные окна под другие пары
}
DEFAULT_WINDOW = (1, 5)

# Заголовки, которые требует Binance P2P API
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
}

# Ограничение параллельных запросов
SEM = asyncio.Semaphore(10)

# Энпоинт официального P2P-API Binance
BINANCE_P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"


async def fetch_ads_binance(client: httpx.AsyncClient, market: StockMarket, symbol: Symbol, side: str, rows: int = 5) -> list[float]:
    """
    Собирает цены первых `rows` объявлений Binance P2P для пары token/fiat и направления BUY/SELL.
    side: "BUY" (мы покупаем у P2P‑продавцов) или "SELL" (мы продаём P2P‑покупателям).
    """
    payload = {
        "asset": symbol.asset_left.asset,
        "fiat": symbol.asset_right.asset,
        "tradeType": side,
        "page": 1,
        "rows": rows,
    }
    async with SEM:
        data = await fetch_data(
            url=market.rates_url.unicode_string(),
            json=payload,
            headers=HEADERS
        )
    items = data.get("data", [])
    prices = []
    for adv_wrapper in items:
        try:
            price = float(adv_wrapper["adv"]["price"])
            prices.append(price)
        except (KeyError, TypeError, ValueError):
            continue
    match side:
        # Для BUY — минимальные объявления (сортируем по возрастанию и берём первые),
        # для SELL — максимальные (по убыванию)
        case "BUY":
            return sorted(prices)[:rows]
        case "SELL":
            return sorted(prices, reverse=True)[:rows]
        case _:
            return []


async def compute_pair_avg_binance(client: httpx.AsyncClient, market: StockMarket, symbol: Symbol) -> dict:
    """
    Возвращает ключ "USDT/RUB" и словарь {"BUY": avg_buy, "SELL": avg_sell}
    """
    window = WINDOW_CONFIG.get(symbol.symbol, {"BUY": DEFAULT_WINDOW, "SELL": DEFAULT_WINDOW})
    buy_list, sell_list = await asyncio.gather(
        fetch_ads_binance(client, market, symbol, side="BUY", rows=window["BUY"][1]),
        fetch_ads_binance(client, market, symbol, side="SELL", rows=window["SELL"][1]),
    )

    def avg(prices: list[float], start: int, end: int) -> float | None:
        sub = prices[start-1 : end]
        return sum(sub) / len(sub) if sub else 0.0
    return {"symbol": symbol.symbol, "price": (avg(buy_list, *window['BUY']), avg(sell_list, *window['SELL']))}

