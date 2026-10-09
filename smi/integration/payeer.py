"""Интеграция Payeer.

Получает пары и tickers из Payeer Trade API; пары API приходят в формате `BASE_QUOTE`.
Обычный спотовый источник: обратные курсы формирует `process_market_data`.
"""

import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import fetch_data, process_market_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_payeer_symbols(stock_market: StockMarket) -> list[Symbol]:
    """Загружает пары Payeer, нормализует `_` и сохраняет прямые/обратные символы."""
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data['pairs']:
        return []
    symbols = [Symbol(asset_left=pair.split('_')[0], asset_right=pair.split('_')[1]) for pair in data["pairs"]]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

@log_execution_time
async def fetch_payeer_rates(stock_market: StockMarket) -> list[SMCourse]:
    """Загружает tickers Payeer и возвращает `list[SMCourse]` через общий обработчик."""
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
