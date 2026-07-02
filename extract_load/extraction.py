import pandas as pd
import requests
import pandas_gbq
import gspread
import logging

logger = logging.getLogger(__name__)


def get_googlesheet_transactions(conf: dict) -> pd.DataFrame:
    """
    Fetch the batch of transactions from Google Sheets.

    Args:
        conf (dict): The dict containing the configurating data and authentications.

    Returns:
        pd.DataFrame: Contains the transactions, if no transactions were extracted, it returns an empty DataFrame.
    """

    try:
        gc = gspread.service_account(filename=conf["json_file_path"])
        sh = gc.open("portfolio_transactions")
        worksheet = sh.worksheet("Transactions")

        transaction_dict = worksheet.get_all_records()
        df_transactions = pd.DataFrame(transaction_dict)

    except:
        logger.exception("Couldn't read transactions from google sheets.")

        df_transactions = pd.DataFrame()

        return df_transactions

    else:

        if df_transactions.empty:
            logger.info("The transactions sheet was empty.")

        else:
            logger.info("Transactions read successfully.")

        return df_transactions


def gbq_get_tickers(conf: dict) -> list:
    """
    Fetch all the currently active tickers from the transactions table.

    Args:
        conf (dict): The dict containing the configurating data and authentications.

    Returns:
        list: Containing the currently active unique tickers.
    """

    try:
        # Filter out closed positions for API ooptimization.
        sql = f"""
        WITH ticker_total AS
        (
        SELECT
        Ticker,
        sum(`Amount + for buy - for sell`) as Current_total
        FROM {conf["transactions_table"]}
        GROUP BY 1
        HAVING sum(`Amount + for buy - for sell`) > 0
        )
        SELECT
        Ticker
        FROM
        ticker_total
        """

        df_tickers = pandas_gbq.read_gbq(
            sql, project_id=conf["project"], credentials=conf["credentials"]
        )

        tickers = df_tickers["Ticker"].to_list()

    except:
        logger.exception("Couldn't fetch the active tickers from Google BigQuery.")

        raise

    else:
        logger.info("Currently active tickers fetched successfully.")

        return tickers


def gbq_get_all_tickers(conf: dict) -> list:
    """
    Fetch all the tickers which were in the transactions list at any point in time.

    Args:
        conf (dict): The dict containing the configurating data and authentications.

    Returns:
        list: Containing all the unique tickers.
    """

    try:
        sql = f"""
        SELECT
        Ticker
        FROM {conf["transactions_table"]}
        GROUP BY 1
        """

        df_tickers = pandas_gbq.read_gbq(
            sql, project_id=conf["project"], credentials=conf["credentials"]
        )

        tickers = df_tickers["Ticker"].to_list()

    except:
        logger.exception("Couldn't fetch all time tickers from Google BigQuery.")

        raise

    else:
        logger.info("All time tickers fetched successfully")

        return tickers


def gbq_get_currencies(conf: dict) -> list:
    """
    Fetch all the active currency codes in the transactions table.

    Args:
        conf (dict): The dict containing the configurating data and authentications.

    Returns:
        list: Containing the currently active unique currencies.
    """

    try:
        # Filter out closed positions for API optimization.
        # Exclude EUR currency because it is the base currency of the portfolio.
        sql = f"""
        WITH ticker_total AS
        (
        SELECT
        Ticker,
        `Currency code`,
        sum(`Amount + for buy - for sell`) as Current_total
        FROM {conf["transactions_table"]}
        GROUP BY 1, 2
        HAVING sum(`Amount + for buy - for sell`) > 0
        )
        SELECT DISTINCT
        `Currency code`
        FROM
        ticker_total
        WHERE `Currency code` != 'EUR'
        """

        df_currencies = pandas_gbq.read_gbq(
            sql, project_id=conf["project"], credentials=conf["credentials"]
        )

        currencies = df_currencies["Currency code"].to_list()

    except:
        logger.exception("Couldn't fetch unique currencies from Google BigQuery.")

        raise

    else:
        logger.info("Unique currencies fetched successfully.")

        return currencies


def api_get_asset_metadata(asset_tickers: list, conf: dict) -> pd.DataFrame:
    """
    Fetch the ticker metadata from the Tiingo API.

    Args:
        asset_tickers (list): Containing the tickers that we need metadata for.
        conf (dict): The dict containing the configurating data and authentications.

    Returns:
        pd.DataFrame: Containing the ticker, the full name of the asset and the exchange code it is traded on.
    """

    try:
        metadata_list = []
        # Iterating because Tiingo only supports singular ticker requests.
        for ticker in asset_tickers:

            headers = {
                "Content-Type": "application/json",
                "Authorization": conf["tiingo_api_token"],
            }

            response = requests.get(
                f"https://api.tiingo.com/tiingo/daily/{ticker}",
                headers=headers,
                timeout=10,
            )

            r = response.json()
            if r:
                metadata = {
                    "tickers": ticker,
                    "asset_name": r["name"],
                    "exchange_code": r["exchangeCode"],
                }
                metadata_list.append(metadata)
            
            else:
                logger.warning(f"{ticker} metadata was not found by Tiingo API.")
            
        df_metadata = pd.DataFrame(metadata_list)

    except:
        logger.exception("Couldn't fetch API asset metadata.")

        raise

    else:
        logger.info("API asset metadata fetched successfully.")

        return df_metadata


def api_get_asset_price(asset_tickers: list, conf: dict) -> pd.DataFrame:
    """
    Fetch the ticker prices from the Tiingo API.

    Args:
        asset_tickers (list): Containing the tickers that we need prices for.
        conf (dict): The dict containing the configurating data and authentications.

    Returns:
        pd.DataFrame: Containing the date of the price, the ticker and the price for that ticker.
    """

    try:
        price_list = []
        # Iterating because Tiingo only supports singular ticker requests.
        for ticker in asset_tickers:

            headers = {
                "Content-Type": "application/json",
                "Authorization": conf["tiingo_api_token"],
            }

            response = requests.get(
                f"https://api.tiingo.com/tiingo/daily/{ticker}/prices",
                headers=headers,
                timeout=10,
            )

            r = response.json()
            if r:
                price = {
                    "dates": r[0]["date"],
                    "tickers": ticker,
                    "price": r[0]["adjClose"],
                }
                price_list.append(price)
            
            else:
                logger.warning(f"{ticker} price was not found by Tiingo API.")

        df_prices = pd.DataFrame(price_list)

    except:
        logger.exception("Couldn't fetch API asset prices.")

        raise

    else:
        logger.info("API asset prices fetched successfully.")

        return df_prices


def api_get_currency_rate(currency_list: list) -> pd.DataFrame:
    """
    Fetch the currency rates from the Frankfurter API.

    Args:
        currency_list (list): Containing the currencies that we need the rates for with EUR base.

    Returns:
        pd.DataFrame: Containing the date of the exchange rate, the currency code and the rate for that currency with EUR base.
    """

    try:
        # The Frankfurter API supports bulk requests, we dont need to iterate.
        currency_list = ",".join(currency_list)

        response = requests.get(
            f"https://api.frankfurter.dev/v2/rates?quotes={currency_list}", timeout=10
        )
        r = response.json()

        currencies = []
        for i in r:
            currencies_row = {
                "dates": i["date"],
                "currency_code": i["quote"],
                "rate": i["rate"],
            }
            currencies.append(currencies_row)

        df_currencies = pd.DataFrame(currencies)

    except:
        logger.exception("Couldn't fetch API currency rates.")

        raise

    else:
        logger.info("API currency rates fetched successfully.")

        return df_currencies
