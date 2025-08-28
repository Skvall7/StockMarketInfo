import logging

import httpx
from datetime import datetime
from typing import List, Any, Callable, Optional, Union

from smi.schemas import Symbol, StockMarket, SMCourse
from config.config import settings

logger = logging.getLogger(settings.title)


async def fetch_data(url: str, method: str = "GET", *, params: Optional[dict[str, Any]] = None,
                     json: Optional[Any] = None, data: Optional[Union[dict[str, Any], bytes, str]] = None,
                     headers: Optional[dict[str, str]] = None, timeout: float = 10.0,) -> Any:
    method = method.upper()
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.request(method, url, params=params, json=json, data=data, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error %s %s: %s", e.request.method, e.response.status_code if e.response else "", getattr(e.response, "text", ""))
        except httpx.RequestError as e:
            logger.warning("Request error %s %s: %s", method, url, e)
        except Exception as e:
            logger.warning("Unexpected error: %s", e)
        return {}

async def process_rate(symbol_obj: Symbol, stock_market: str, price: float|tuple[float, float], timestamp: datetime, p2p=False) -> List[SMCourse]:
    """Создает основной и обратный курсы для заданного символа."""
    rates = []
    rate = SMCourse(
        symbol=symbol_obj.symbol,
        stock_market=stock_market,
        course=price if not p2p else price[0],
        calculated=price < 1 if not p2p else price[0] < 1,
        updated=timestamp
    )
    rates.append(rate)
    reverse_rate = SMCourse(
        symbol=Symbol(asset_left=symbol_obj.asset_right.asset, asset_right=symbol_obj.asset_left.asset).symbol,
        stock_market=stock_market,
        course=1 / price if not p2p else 1 / price[1],
        calculated=(1 / price) <= 1 if not p2p else (1 / price[1]) <= 1,
        updated=timestamp
    )
    rates.append(reverse_rate)
    return rates


async def process_market_data(stock_market: StockMarket, data: list[dict], extract_symbol: Callable[[dict], str],
                              extract_price: Callable[[dict], float|tuple[float, float]], p2p=False) -> list[SMCourse]:
    """Универсальная функция для обработки данных рынка."""
    rates = []
    timestamp = datetime.now()
    for item in data:
        symbol_str = extract_symbol(item)
        symbol_obj = next((symbol for symbol in stock_market.symbols if symbol.symbol == symbol_str), None)
        if symbol_obj:
            price = extract_price(item)
            if p2p:
                if not price[0] or not price[1]:
                    continue
                rates += await process_rate(symbol_obj=symbol_obj, stock_market=stock_market.name, price=price, timestamp=timestamp, p2p=p2p)
            else:
                if not price:
                    continue
                rates += await process_rate(symbol_obj=symbol_obj, stock_market=stock_market.name, price=price, timestamp=timestamp)
    return rates
