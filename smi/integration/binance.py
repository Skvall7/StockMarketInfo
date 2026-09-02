"""Интеграция Binance Spot.

Получает торгуемые пары через `exchangeInfo`, курсы через `ticker/price`.
Обычный спотовый источник: обратные курсы формирует `process_market_data`.
"""

import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import fetch_data, process_market_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_binance_symbols(stock_market: StockMarket) -> list[Symbol]:
    """Загружает торгуемые spot-пары Binance и сохраняет их в `stock_market.symbols`."""
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data['symbols']:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [
        Symbol(asset_left=item['baseAsset'], asset_right=item['quoteAsset'])
        for item in data['symbols']
        if item['status'] == 'TRADING'  # Проверка торгуется ли пара
    ]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

@log_execution_time
async def fetch_binance_rates(stock_market: StockMarket) -> list[SMCourse]:
    """Загружает цены Binance и возвращает `list[SMCourse]` через общий обработчик."""
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
