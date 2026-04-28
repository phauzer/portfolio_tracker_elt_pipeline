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
        "table": os.environ.get("dataset_name") + "." + "raw_transactions",
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
        conf["table"],
        project_id=conf["project"],
        if_exists="append",
        credentials=conf["credentials"],
    )

    worksheet.batch_clear(["A2:D1000"])


def gbq_get_tickers(conf: dict) -> list:

    sql = f"""
    WITH ticker_total AS
    (
    SELECT
    Ticker,
    sum(Amount) as Current_total
    FROM {conf['table']}
    GROUP BY 1
    HAVING sum(Amount) > 0
    )
    SELECT
    Ticker
    FROM
    ticker_total
    """

    df_tickers = pandas_gbq.read_gbq(
        sql, project_id=conf["project"], credentials=conf["credentials"]
    )

    df_tickers = df_tickers["Ticker"].to_list()

    return df_tickers


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
        price = {"dates": r[0]["date"], "tickers": ticker, "price": r[0]["close"]}
        price_list.append(price)

    df_prices = pd.DataFrame(price_list)

    return df_prices


if __name__ == "__main__":
    conf = get_conf()
    tickers = gbq_get_tickers(conf)
    print(api_get_asset_price(tickers, conf))
