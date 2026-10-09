"""Интеграция Abcex Spot.

Получает активные пары через список инструментов и справочник активов публичного API v2.
Курсы берутся из lastPrice тикеров; обратные курсы формирует process_market_data.
"""

import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import fetch_data, process_market_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_abcex_symbols(stock_market: StockMarket) -> list[Symbol]:
    """Загружает активные spot-пары Abcex и сохраняет прямые/обратные символы."""
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data:
        logger.warning(f"Error data: {data}")
        return []
    assets = await fetch_data(settings.abcex_assets_url.unicode_string())
    if not assets:
        logger.warning(f"Error data: {assets}")
        return []
    asset_codes = {item['assetId']: item['code'] for item in assets}
    symbols = [
        Symbol(asset_left=asset_codes[item['baseAssetId']], asset_right=asset_codes[item['quotedAssetId']])
        for item in data
        if item['isListed'] and item['isActive']
    ]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = symbols + rev_symbols
    return symbols


@log_execution_time
async def fetch_abcex_rates(stock_market: StockMarket) -> list[SMCourse]:
    """Загружает последние цены Abcex и возвращает курсы через общий обработчик."""
    data = await fetch_data(stock_market.rates_url.unicode_string())
    if not data or not data.get('tickers'):
        logger.warning(f"Error data: {data}")
        return []
    return await process_market_data(
        stock_market,
        data['tickers'],
        extract_symbol=lambda item: item['symbol'].upper(),
        extract_price=lambda item: float(item['lastPrice'])
    )
