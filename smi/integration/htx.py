"""Интеграция HTX Spot.

Получает online-символы через настройки HTX, курсы через общий список tickers.
Обычный спотовый источник: обратные курсы формирует `process_market_data`.
"""

import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import fetch_data, process_market_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_htx_symbols(stock_market: StockMarket) -> list[Symbol]:
    """Загружает online-пары HTX и сохраняет их в `stock_market.symbols`."""
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data['data']:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [
        Symbol(asset_left=item["bc"], asset_right=item["qc"])
        for item in data["data"]
        if item['state'] == 'online'    # Проверка торгуется ли пара
    ]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

@log_execution_time
async def fetch_htx_rates(stock_market: StockMarket) -> list[SMCourse]:
    """Загружает tickers HTX и возвращает `list[SMCourse]` через общий обработчик."""
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
