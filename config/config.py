import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

from smi.schemas import StockMarket


class Settings(BaseSettings):
    # Загрузка переменных окружения из файла .env
    model_config = SettingsConfigDict(env_file='important/.env', env_file_encoding='utf-8')

    # Параметр окружения (development, production, test)
    environment: str = 'production'

    # Основные параметры приложения
    version: str = '0.2.0'
    title: str = 'Stock market info service'
    description: str = 'Stock market info service - collects information about cryptocurrency exchange rates from exchanges, as well as information about tokens'

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
        name='SelfCourse',
        info_url='https://selfcourse.com/',
        rates_url='https://selfcourse.com/',
        requests_sleep=60,
        requests_per_day=86400,
    )

    goatx: StockMarket = StockMarket(
        name='GoatX',
        info_url='https://goatx.me/',
        rates_url='https://goatx.me/',
        requests_sleep=60,
        requests_per_day=86400,
    )

    bybit: StockMarket = StockMarket(
        name='Bybit',
        info_url='https://api.bybit.com/v5/market/instruments-info?category=spot',
        rates_url='https://api.bybit.com/v5/market/tickers?category=spot',
        requests_sleep=60,
        requests_per_day=86400,
    )

    bybit_p2p: StockMarket = StockMarket(
        name='Bybit_p2p',
        info_url='https://api2.bybit.com/fiat/otc/item/online',
        rates_url='https://api2.bybit.com/fiat/otc/item/online',
        requests_sleep=60,
        requests_per_day=1440,
    )

    # https://rapira.readme.io/reference/intro
    rapira: StockMarket = StockMarket(
        name='Rapira',
        info_url='https://api.rapira.net/open/market/pairs',
        rates_url='https://api.rapira.net/open/market/rates',
        requests_sleep=60,
        requests_per_day=144000,
    )

    binance_p2p: StockMarket = StockMarket(
        name='Binance_p2p',
        info_url='https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search',
        rates_url='https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search',
        requests_sleep=60,
        requests_per_day=1440,
    )


# Инициализация настроек
settings = Settings()
all_rates = {}
settings.configure_logging()
