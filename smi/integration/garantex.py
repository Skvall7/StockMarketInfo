"""Интеграция Garantex.

Получает список рынков из `/markets`, а курс каждой пары берет отдельным запросом
к `/trades?market=...&limit=1`. Обратные курсы формирует `process_market_data`.
"""

import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import fetch_data, process_market_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_garantex_symbols(stock_market: StockMarket) -> list[Symbol]:
    """Загружает рынки Garantex и сохраняет прямые и обратные символы."""
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data[0]['ask_unit']:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [Symbol(asset_left=item['ask_unit'], asset_right=item['bid_unit']) for item in data]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

@log_execution_time
async def fetch_garantex_rates(stock_market: StockMarket) -> list[SMCourse]:
    """Последовательно получает последний trade price по каждому символу Garantex."""
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
