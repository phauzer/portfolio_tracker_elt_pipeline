from dotenv import load_dotenv
import os
from google.oauth2 import service_account
import logging

root_log = logging.getLogger()
root_log.setLevel(logging.INFO)
formatting = logging.Formatter(
    "%(asctime)s-%(levelname)s-%(name)s-%(funcName)s-%(message)s"
)
file = logging.FileHandler("python_logs/data_extract_load.log")
file.setFormatter(formatting)
root_log.addHandler(file)

logger = logging.getLogger(__name__)


def get_conf() -> dict:
    """
    Fetch the variables from .env file.

    Returns:
        dict: Containing the api token, GBQ project IDs and credentials doc.
    """

    try:
        load_dotenv()

        conf = {
            "tiingo_api_token": os.environ.get("tiingo_api_token"),
            "json_file_path": os.environ.get("gc_service_account_json_path"),
            "credentials": service_account.Credentials.from_service_account_file(
                os.environ.get("gc_service_account_json_path")
            ),
            "project": os.environ.get("project_id"),
            "dataset": os.environ.get("dataset_name"),
            "transactions_table": os.environ.get("dataset_name")
            + "."
            + "raw_transactions",
        }

    except:
        logger.exception("Couldn't read .env file.")

        raise

    else:
        logger.info("Config read successfully from .env file.")

        return conf
