import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

from smi.schemas import StockMarket


class Settings(BaseSettings):
    # Загрузка переменных окружения из файла .env
    model_config = SettingsConfigDict(env_file='important/.env', env_file_encoding='utf-8')

    # Параметр окружения (development, production, test)
    environment: str = 'production'

    # Основные параметры приложения
    version: str = '0.1.0'
    title: str = 'Stock market info service'
    description: str = 'Stock market info service - collects information about cryptocurrency exchange rates from exchanges, as well as information about tokens'

    # Параметры Kafka
    kafka_connections: list[str]

    # Параметры логгера
    log_level: str = 'INFO'  # Уровень логирования по умолчанию
    log_file: str = 'var/logs/smi.log'

    def configure_logging(self):
        logging.basicConfig(
            level=self.log_level,
            format=f'%(asctime)s %(levelname)s {self.title} - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        logging.getLogger(self.title).setLevel(self.log_level)

    # Параметры бирж
    binance: StockMarket = StockMarket(
        name='Binance',
        info_url='https://api.binance.com/api/v3/exchangeInfo',
        rates_url='https://api.binance.com/api/v3/ticker/price',
        requests_sleep=60,
        requests_per_day=86400,
    )

    garantex: StockMarket = StockMarket(
        name='Garantex',
        info_url='https://garantex.org/api/v2/markets',
        rates_url='https://garantex.org/api/v2/trades',
        requests_sleep=60,
        requests_per_day=1728,
    )

    payeer: StockMarket = StockMarket(
        name='Payeer',
        info_url='https://payeer.com/api/trade/info',
        rates_url='https://payeer.com/api/trade/ticker',
        requests_sleep=60,
        requests_per_day=86400,
    )

    htx: StockMarket = StockMarket(
        name='HTX',
        info_url='https://api.huobi.pro/v1/settings/common/symbols',
        rates_url='https://api.huobi.pro/market/tickers',
        requests_sleep=60,
        requests_per_day=86400,
    )

    cbr: StockMarket = StockMarket(
        name='CBR',
        info_url='https://www.cbr-xml-daily.ru/daily_json.js',
        rates_url='https://www.cbr-xml-daily.ru/daily_json.js',
        requests_sleep=60,
        requests_per_day=86400,
    )

    wmg: StockMarket = StockMarket(
        name='WMGlobus',
        info_url='https://wmglobus.com/',
        rates_url='https://wmglobus.com/',
        requests_sleep=60,
        requests_per_day=86400,
    )


# Инициализация настроек
settings = Settings()
settings.configure_logging()
