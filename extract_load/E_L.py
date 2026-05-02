import requests
from dotenv import load_dotenv
import os
import pandas as pd
import gspread
import pandas_gbq
from google.oauth2 import service_account


def get_conf() -> dict:

    load_dotenv()

    conf = {
        "tiingo_api_token": os.environ.get("tiingo_api_token"),
        "json_file_path": os.environ.get("gc_service_account_json_path"),
        "credentials": service_account.Credentials.from_service_account_file(
            os.environ.get("gc_service_account_json_path")
        ),
        "project": os.environ.get("project_id"),
        "dataset": os.environ.get("dataset_name"),
        "transactions_table": os.environ.get("dataset_name") + "." + "raw_transactions",
    }

    return conf


def googlesheet_to_gbq(conf: dict) -> None:

    gc = gspread.service_account(filename=conf["json_file_path"])

    sh = gc.open("portfolio_transactions")
    worksheet = sh.worksheet("Transactions")
    transaction_dict = worksheet.get_all_records()

    df_transactions = pd.DataFrame(transaction_dict)

    pandas_gbq.to_gbq(
        df_transactions,
        conf["transactions_table"],
        project_id=conf["project"],
        if_exists="append",
        credentials=conf["credentials"],
    )

    worksheet.batch_clear(["A2:E1000"])


def gbq_get_tickers(conf: dict) -> list:

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

    return tickers


def gbq_get_all_tickers(conf: dict) -> list:

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

    return tickers


def gbq_get_currencies(conf: dict) -> list:

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

    return currencies


def api_get_asset_metadata(asset_tickers: list, conf: dict) -> pd.DataFrame:

    metadata_list = []
    for ticker in asset_tickers:

        headers = {
            "Content-Type": "application/json",
            "Authorization": conf["tiingo_api_token"],
        }

        response = requests.get(
            f"https://api.tiingo.com/tiingo/daily/{ticker}", headers=headers
        )

        r = response.json()
        metadata = {
            "tickers": ticker,
            "asset_name": r["name"],
            "exchange_code": r["exchangeCode"],
        }
        metadata_list.append(metadata)

    df_metadata = pd.DataFrame(metadata_list)
    return df_metadata


def api_get_asset_price(asset_tickers: list, conf: dict) -> pd.DataFrame:

    price_list = []
    for ticker in asset_tickers:

        headers = {
            "Content-Type": "application/json",
            "Authorization": conf["tiingo_api_token"],
        }

        response = requests.get(
            f"https://api.tiingo.com/tiingo/daily/{ticker}/prices", headers=headers
        )

        r = response.json()
        price = {"dates": r[0]["date"], "tickers": ticker, "price": r[0]["adjClose"]}
        price_list.append(price)

    df_prices = pd.DataFrame(price_list)

    return df_prices


def api_get_currency_rate(currency_list: list) -> pd.DataFrame:

    currency_list = ",".join(currency_list)

    response = requests.get(
        f"https://api.frankfurter.dev/v2/rates?quotes={currency_list}"
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

    return df_currencies


def asset_names_to_gbq(names: pd.DataFrame, conf: dict) -> None:

    table = conf["dataset"] + "." + "raw_asset_metadatas"
    pandas_gbq.to_gbq(
        names,
        table,
        project_id=conf["project"],
        if_exists="replace",
        credentials=conf["credentials"],
    )


def asset_prices_to_gbq(prices: pd.DataFrame, conf: dict) -> None:

    table = conf["dataset"] + "." + "raw_asset_prices"
    pandas_gbq.to_gbq(
        prices,
        table,
        project_id=conf["project"],
        if_exists="append",
        credentials=conf["credentials"],
    )


def currency_rates_to_gbq(currencies: pd.DataFrame, conf: dict) -> None:

    table = conf["dataset"] + "." + "raw_currency_exchange_price"
    pandas_gbq.to_gbq(
        currencies,
        table,
        project_id=conf["project"],
        if_exists="append",
        credentials=conf["credentials"],
    )


def main() -> None:

    conf = get_conf()
    googlesheet_to_gbq(conf)
    tickers = gbq_get_tickers(conf)
    all_tickers = gbq_get_all_tickers(conf)
    currencies = gbq_get_currencies(conf)
    asset_metadatas = api_get_asset_metadata(all_tickers, conf)
    asset_prices = api_get_asset_price(tickers, conf)
    currency_rates = api_get_currency_rate(currencies)
    asset_names_to_gbq(asset_metadatas, conf)
    asset_prices_to_gbq(asset_prices, conf)
    currency_rates_to_gbq(currency_rates, conf)


if __name__ == "__main__":
    main()
