"""Интеграция GoatX.

Текущая реализация не ходит во внешний API и отдает фиксированную пару USDT/AZN = 1.75.
Обратный курс формирует `process_market_data`.
"""

import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import process_market_data
from smi.schemas import SMCourse, StockMarket, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_goatx_symbols(stock_market: StockMarket) -> list[Symbol]:
    """Создает статический список символов GoatX и сохраняет обратную пару."""
    symbols = [Symbol(asset_left='USDT', asset_right='AZN')]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols


@log_execution_time
async def fetch_goatx_rates(stock_market: StockMarket) -> list[SMCourse]:
    """Возвращает фиксированный курс USDT/AZN через общий обработчик."""
    return await process_market_data(
        stock_market,
        [{'symbol': 'USDTAZN', 'value': 1.75}],
        extract_symbol=lambda item: item['symbol'].upper(),
        extract_price=lambda item: float(item['value'])
    )
