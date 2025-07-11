import logging
import asyncio
import httpx

from statistics import mean
from typing import Optional, Any

from config.config import settings
from smi.schemas import Symbol, StockMarket

logger = logging.getLogger(settings.title)

# Параметры окон усреднения: можно добавить индивидуальные
WINDOW_CONFIG = {
    "USDTRUB": {'BUY': (3,5), 'SELL': (3,5)},
}
DEFAULT_WINDOW = (2, 4)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.bybit.com"
}

SEM = asyncio.Semaphore(20)

async def fetch_data_post(client: httpx.AsyncClient, url: str, json_payload: dict[str, Any], headers: dict[str, str], timeout: float = 10.0) -> dict[str, Any]:
    """
    Универсально шлёт POST-запрос и возвращает распарсенный JSON.
    Не закрывает клиент, ошибки пробрасывает наверх.
    """
    resp = await client.post(url, json=json_payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

async def fetch_ads(client: httpx.AsyncClient, market: StockMarket, symbol: Symbol, side: str) -> list[float]:
    # TODO требуеться доадоптировать p2p, в частности запросы
    prices: list[float] = []
    page = 1
    size = 50
    while True:
        payload = {"tokenId": symbol.asset_left.asset, "currencyId": symbol.asset_right.asset, "side": side, "page": str(page), "size": str(size)}
        async with SEM:
            data = await fetch_data_post(client=client, url=market.rates_url.unicode_string(), json_payload=payload, headers=HEADERS,)
        items = data.get("result", {}).get("items", [])
        if not items:
            break
        for item in items:
            if "VA" not in item.get("authTag", []):
                continue
            try:
                prices.append(float(item["price"]))
            except (KeyError, ValueError):
                continue
        page += 1
    return sorted(prices) if side == "1" else sorted(prices, reverse=True)

async def compute_pair_avg(client: httpx.AsyncClient, market: StockMarket, symbol: Symbol ) -> dict[str, tuple[Optional[float], Optional[float]]]:
    window = WINDOW_CONFIG.get(symbol.symbol, {'BUY': DEFAULT_WINDOW, 'SELL': DEFAULT_WINDOW})
    buy_list, sell_list = await asyncio.gather(fetch_ads(client, market, symbol, side="1"), fetch_ads(client, market, symbol, side="0"))

    def avg(prices: list[float], start: int, end: int) -> float:
        sub = prices[start-1:end]
        return mean(sub) if sub else 0.0
    # print(f"!!!!! {symbol.symbol} {avg(buy_list, *window['BUY'])} {avg(sell_list, *window['SELL'])}")
    return {"symbol": symbol.symbol, "price": (avg(buy_list, *window['BUY']), avg(sell_list, *window['SELL']))}

