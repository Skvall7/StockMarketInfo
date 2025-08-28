import logging

from config.app import log_execution_time
from config.config import settings
from smi.parser import fetch_data, process_market_data
from smi.schemas import StockMarket, SMCourse, Symbol

logger = logging.getLogger(settings.title)


@log_execution_time
async def fetch_bybit_symbols(stock_market: StockMarket) -> list[Symbol]:
    data = await fetch_data(stock_market.info_url.unicode_string())
    if not data or not data['result']:
        logger.warning(f"Error data: {data}")
        return []
    symbols = [
        Symbol(asset_left=item["baseCoin"], asset_right=item["quoteCoin"])
        for item in data["result"]['list']
        if item['status'] == 'Trading'    # Проверка торгуется ли пара
    ]
    rev_symbols = [Symbol(asset_left=symbol.asset_right, asset_right=symbol.asset_left) for symbol in symbols]
    stock_market.symbols = []
    stock_market.symbols = symbols + rev_symbols
    return symbols

@log_execution_time
async def fetch_bybit_rates(stock_market: StockMarket) -> list[SMCourse]:
    data = await fetch_data(stock_market.rates_url.unicode_string())
    if not data or not data['result']:
        logger.warning(f"Error data: {data}")
        return []
    return await process_market_data(
        stock_market,
        data['result']['list'],
        extract_symbol=lambda item: item['symbol'].upper(),
        extract_price=lambda item: float(item['lastPrice'])
    )
