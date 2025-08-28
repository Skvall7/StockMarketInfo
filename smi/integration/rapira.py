import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import fetch_data, process_market_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_rapira_symbols(stock_market: StockMarket) -> list[Symbol]:
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [
        Symbol(asset_left=item["coinSymbol"], asset_right=item["baseSymbol"])
        for item in data
        if item['exchangeable'] == True  # Проверка торгуется ли пара
    ]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

@log_execution_time
async def fetch_rapira_rates(stock_market: StockMarket) -> list[SMCourse]:
    data = await fetch_data(stock_market.rates_url.unicode_string())
    if not data or not data['data']:
        logger.warning(f"Error data: {data}")
        return []
    pairs_data = [{'symbol': value['symbol'].replace('/', ''), 'close': value['close']} for value in data['data']]
    return await process_market_data(
        stock_market,
        pairs_data,
        extract_symbol=lambda item: item['symbol'].upper(),
        extract_price=lambda item: float(item['close'])
    )