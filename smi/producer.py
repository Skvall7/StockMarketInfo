import asyncio

from config.app import broker, log_execution_time
from config.config import settings


async def publish_in_batches(rates, batch_size=100):
    batch = []
    for rate in rates:
        batch.append((rate.symbol.symbol, rate.dict()))
        if len(batch) >= batch_size:
            await asyncio.gather(*[
                broker.publish(message, key=key, topic="webstudio.smi.rates.stream")
                for key, message in batch
            ])
            batch.clear()
    if batch:
        await asyncio.gather(*[
            broker.publish(message, key=key, topic="webstudio.smi.rates.stream")
            for key, message in batch
        ])


@log_execution_time
async def collect_rates(fetch_function, stock_market):
    # Публикация курсов бирж
    rates = await fetch_function(stock_market)
    await publish_in_batches(rates)


async def push_sm_info():
    # Публикация информации о биржах
    stock_markets = [settings.binance, settings.htx, settings.payeer, settings.garantex, settings.cbr, settings.wmg]
    for stock_market in stock_markets:
        await broker.publish(stock_market.model_dump(), key=stock_market.name, topic="webstudio.smi.stockmarkets.etl.assets")

