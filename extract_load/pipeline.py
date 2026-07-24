from apis.bigquery import BigQueryApi
from apis.frankfurter import FrankfurterFxFetcher
from apis.tiingo import TiingoApiFetcher
from apis.googlsheet import GoogleSheetApi
from pandas import DataFrame
from os import environ
import logging

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)
formatting = logging.Formatter(
    "%(asctime)s-%(levelname)s-%(name)s-%(funcName)s-%(message)s"
)
file = logging.FileHandler("python_logs/data_extract_load.log")
file.setFormatter(formatting)
root_log.addHandler(file)

console_log = logging.StreamHandler()
console_log.setFormatter(formatting)
root_log.addHandler(console_log)

logger = logging.getLogger(__name__)


class Pipeline:

    def __init__(self):

        self.bigquery = BigQueryApi()
        self.frankfurter = FrankfurterFxFetcher()
        self.tiingo = TiingoApiFetcher()
        self.googlesheet = GoogleSheetApi()
        self.dataset = environ.get("dataset_name")

    def run(self) -> None:

        transactions = self._get_transactions()
        self.bigquery.load_data(transactions, self.dataset,"raw_transactions", "append")
        active_tickers = self._gbq_get_active_tickers()
        all_ticker = self._gbq_get_all_tickers()
        currencies = self._gbq_get_currencies()
        metadata = self._api_get_metadata(all_ticker)
        asset_prices = self._api_get_prices(active_tickers)
        currency_rates = self._api_get_currency_rates(currencies)
        self.bigquery.load_data(metadata, self.dataset, "raw_asset_metadatas", "replace")
        self.bigquery.load_data(asset_prices, self.dataset, "raw_asset_prices", "append")
        self.bigquery.load_data(currency_rates, self.dataset, "raw_currency_exchange_price", "append")

    def _get_transactions(self) -> DataFrame:

        transactions = self.googlesheet.extract()
        self.googlesheet.make_worksheet("archived", 10000, 5)
        self.googlesheet.append_data("archived", transactions)
        self.googlesheet.sheet_cleanup("A2", "E1000")
        df_trans = DataFrame(transactions)

        return df_trans

    def _gbq_get_active_tickers(self) -> list:

        sql = f"""
        WITH ticker_total AS
        (
        SELECT
        Ticker,
        sum(`Amount + for buy - for sell`) as Current_total
        FROM {self.dataset + "." + "raw_transactions"}
        GROUP BY 1
        HAVING sum(`Amount + for buy - for sell`) > 0
        )
        SELECT
        Ticker
        FROM
        ticker_total
        """

        df_tickers = self.bigquery.run_sql(sql)
        tickers = df_tickers["Ticker"].to_list()

        return tickers

    def _gbq_get_all_tickers(self) -> list:

        sql = f"""
        SELECT
        Ticker
        FROM {self.dataset + "." + "raw_transactions"}
        GROUP BY 1
        """

        df_tickers = self.bigquery.run_sql(sql)
        tickers = df_tickers["Ticker"].to_list()

        return tickers

    def _gbq_get_currencies(self) -> list:

        sql = f"""
        WITH ticker_total AS
        (
        SELECT
        Ticker,
        `Currency code`,
        sum(`Amount + for buy - for sell`) as Current_total
        FROM {self.dataset + "." + "raw_transactions"}
        GROUP BY 1, 2
        HAVING sum(`Amount + for buy - for sell`) > 0
        )
        SELECT DISTINCT
        `Currency code`
        FROM
        ticker_total
        WHERE `Currency code` != 'EUR'
        """

        df_currencies = self.bigquery.run_sql(sql)

        currencies = df_currencies["Currency code"].to_list()

        return currencies

    def _api_get_metadata(self, tickers: list) -> DataFrame:

        metadata_list = self.tiingo.get_metadata(tickers)
        df_metadata = DataFrame(metadata_list)

        return df_metadata

    def _api_get_prices(self, tickers: list) -> DataFrame:
    
        prices_list = self.tiingo.get_prices(tickers)
        df_prices = DataFrame(prices_list)

        return df_prices

    def _api_get_currency_rates(self, currencies: list) -> DataFrame:

        currencies_list = self.frankfurter.get_prices(currencies)
        df_currencies = DataFrame(currencies_list)

        return df_currencies


