import asyncio
import logging

import httpx
from datetime import datetime
from typing import List, Any, Dict, Callable

from config.app import log_execution_time
from smi.schemas import Symbol, StockMarket, SMCourse
from config.config import settings

logger = logging.getLogger(settings.title)


async def fetch_data(url: str) -> Any:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.warning(f"An error occurred: {e}")
        return {}


@log_execution_time
async def fetch_binance_symbols(stock_market: StockMarket) -> List[Symbol]:
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data['symbols']:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [
        Symbol(asset_left=item['baseAsset'], asset_right=item['quoteAsset'])
        for item in data['symbols']
        if item['status'] == 'TRADING'  # Проверка торгуется ли пара
    ]
    stock_market.symbols = []
    stock_market.symbols = symbols
    return symbols


@log_execution_time
async def fetch_garantex_symbols(stock_market: StockMarket) -> List[Symbol]:
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data[0]['ask_unit']:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [Symbol(asset_left=item['ask_unit'], asset_right=item['bid_unit']) for item in data]
    stock_market.symbols = []
    stock_market.symbols = symbols
    return symbols


@log_execution_time
async def fetch_payeer_symbols(stock_market: StockMarket) -> List[Symbol]:
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data['pairs']:
        return []
    symbols = [Symbol(asset_left=pair.split('_')[0], asset_right=pair.split('_')[1]) for pair in data["pairs"]]
    stock_market.symbols = []
    stock_market.symbols = symbols
    return symbols


@log_execution_time
async def fetch_htx_symbols(stock_market: StockMarket) -> List[Symbol]:
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data['data']:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [
        Symbol(asset_left=item["bc"], asset_right=item["qc"])
        for item in data["data"]
        if item['state'] == 'online'    # Проверка торгуется ли пара
    ]
    stock_market.symbols = []
    stock_market.symbols = symbols
    return symbols


@log_execution_time
async def fetch_cbr_symbols(stock_market: StockMarket) -> List[Symbol]:
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data['Valute']:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [Symbol(asset_left=code, asset_right='RUB')for code, currency_data in data["Valute"].items()]
    stock_market.symbols = []
    stock_market.symbols = symbols
    return symbols


@log_execution_time
async def fetch_wmg_symbols(stock_market: StockMarket) -> List[Symbol]:
    symbols = [Symbol(asset_left='USDT', asset_right='USD')]
    stock_market.symbols = []
    stock_market.symbols = symbols
    return symbols


async def fetch_all_symbols() -> List[Symbol]:
    fetch_tasks = [
        fetch_binance_symbols(settings.binance),
        fetch_garantex_symbols(settings.garantex),
        fetch_payeer_symbols(settings.payeer),
        fetch_htx_symbols(settings.htx),
        fetch_cbr_symbols(settings.cbr),
        fetch_wmg_symbols(settings.wmg)
    ]
    results = await asyncio.gather(*fetch_tasks)
    symbol_set = {symbol.symbol: symbol for symbol_list in results for symbol in symbol_list}
    return list(symbol_set.values())


async def process_rate(symbol_obj: Symbol, stock_market: str, price: float, timestamp: datetime) -> List[SMCourse]:
    """Создает основной и обратный курсы для заданного символа."""
    rates = []
    rate = SMCourse(
        symbol=symbol_obj,
        stock_market=stock_market,
        course=price,
        calculated=price < 1,
        updated=timestamp
    )
    rates.append(rate)
    reverse_rate = SMCourse(
        symbol=Symbol(asset_left=symbol_obj.asset_right.asset, asset_right=symbol_obj.asset_left.asset),
        stock_market=stock_market,
        course=1 / price,
        calculated=(1 / price) <= 1,
        updated=timestamp
    )
    rates.append(reverse_rate)
    return rates


async def process_market_data(stock_market: StockMarket, data: List[Dict], extract_symbol: Callable[[Dict], str], extract_price: Callable[[Dict], float]) -> List[SMCourse]:
    """Универсальная функция для обработки данных рынка."""
    rates = []
    timestamp = datetime.now()
    for item in data:
        symbol_str = extract_symbol(item)
        symbol_obj = next((symbol for symbol in stock_market.symbols if symbol.symbol == symbol_str), None)
        if symbol_obj:
            price = extract_price(item)
            if not price:
                continue
            rates += await process_rate(symbol_obj=symbol_obj, stock_market=stock_market.name, price=price, timestamp=timestamp)
    return rates


@log_execution_time
async def fetch_binance_rates(stock_market: StockMarket) -> List[SMCourse]:
    data = await fetch_data(stock_market.rates_url.unicode_string())
    if not data or not data[0]['price']:
        logger.warning(f"Error data: {data}")
        return []
    return await process_market_data(
        stock_market,
        data,
        extract_symbol=lambda item: item['symbol'],
        extract_price=lambda item: float(item['price'])
    )


@log_execution_time
async def fetch_htx_rates(stock_market: StockMarket) -> List[SMCourse]:
    data = await fetch_data(stock_market.rates_url.unicode_string())
    if not data or not data['data']:
        logger.warning(f"Error data: {data}")
        return []
    return await process_market_data(
        stock_market,
        data['data'],
        extract_symbol=lambda item: item['symbol'].upper(),
        extract_price=lambda item: float(item['close'])
    )


@log_execution_time
async def fetch_garantex_rates(stock_market: StockMarket) -> List[SMCourse]:
    all_data = []
    for symbol in stock_market.symbols:
        market = symbol.symbol.lower()
        url = f"{stock_market.rates_url.unicode_string()}?market={market}&limit=1"
        data = await fetch_data(url)
        if data and data[0]['price']:
            all_data.append({'symbol': symbol.symbol, 'price': float(data[0]['price'])})
        else:
            logger.warning(f"Error data: {data}")
    return await process_market_data(
        stock_market,
        all_data,
        extract_symbol=lambda item: item['symbol'],
        extract_price=lambda item: item['price']
    )


@log_execution_time
async def fetch_payeer_rates(stock_market: StockMarket) -> List[SMCourse]:
    data = await fetch_data(stock_market.rates_url.unicode_string())
    if not data or not data['pairs']:
        logger.warning(f"Error data: {data}")
        return []
    pairs_data = [{'symbol': key.replace('_', ''), 'last': value['last']} for key, value in data['pairs'].items()]
    return await process_market_data(
        stock_market,
        pairs_data,
        extract_symbol=lambda item: item['symbol'],
        extract_price=lambda item: float(item['last']) if item['last'] else 0
    )


@log_execution_time
async def fetch_cbr_rates(stock_market: StockMarket) -> List[SMCourse]:
    data = await fetch_data(stock_market.rates_url.unicode_string())
    if not data or not data['Valute']:
        logger.warning(f"Error data: {data}")
        return []
    pairs_data = [{'symbol': f'{key}RUB', 'value': float(value['Value']) / float(value['Nominal'])} for key, value in data['Valute'].items()]
    return await process_market_data(
        stock_market,
        pairs_data,
        extract_symbol=lambda item: item['symbol'].upper(),
        extract_price=lambda item: float(item['value'])
    )


@log_execution_time
async def fetch_wmg_rates(stock_market: StockMarket) -> List[SMCourse]:
    return await process_market_data(
        stock_market,
        [{'symbol': 'USDTUSD', 'value': 1}],
        extract_symbol=lambda item: item['symbol'].upper(),
        extract_price=lambda item: float(item['value'])
    )
