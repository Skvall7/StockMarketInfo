import asyncio

from config.app import app, logger
from config.config import settings
from smi.parser import fetch_all_symbols, fetch_binance_rates, fetch_garantex_rates, fetch_payeer_rates, \
    fetch_htx_rates, fetch_cbr_rates, fetch_wmg_rates
from smi.producer import collect_rates, push_sm_info


async def update_course(stock_market, fetch_course_func):
    """Обновляет курсы бирж с заданным интервалом."""
    while True:
        await collect_rates(fetch_course_func, stock_market)
        logger.info(f'Updated {stock_market.name} rates.')
        await asyncio.sleep(stock_market.requests_sleep)


async def update_info():
    """Обновляет символы биржи с заданным интервалом."""
    while True:
        await fetch_all_symbols()
        await push_sm_info()
        logger.info(f'Updated all symbols.')
        await asyncio.sleep(600)


@app.after_startup
async def initialize():
    tasks = [
        update_info(),
        update_course(settings.binance, fetch_binance_rates),
        update_course(settings.garantex, fetch_garantex_rates),
        update_course(settings.payeer, fetch_payeer_rates),
        update_course(settings.htx, fetch_htx_rates),
        update_course(settings.cbr, fetch_cbr_rates),
        update_course(settings.wmg, fetch_wmg_rates),
    ]
    await asyncio.gather(*tasks)
