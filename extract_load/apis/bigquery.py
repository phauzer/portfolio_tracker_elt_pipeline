from os import environ
from google.oauth2 import service_account
from pandas import DataFrame
import pandas_gbq
from logging import getLogger

logger = getLogger(__name__)

class BigQueryApi:

    def __init__(self, service_account_filename: str = environ.get("gc_service_account_json_path"), project_id: str = environ.get("project_id")) -> None:

        self.service_account = service_account_filename
        self.project_id = project_id
        self.credentials = service_account.Credentials.from_service_account_file(self.service_account)

    def run_sql(self, sql_query: str) -> DataFrame:
        """
        Run sql query in Google BigQuery.
    
        Args:
            sql_query (str): The SQL query that needs to be ran.
        """

        try:
            df = pandas_gbq.read_gbq(
                        sql_query, project_id=self.project_id, credentials=self.credentials
                    )

        except:
            logger.exception(f"Couldn't fetch the requested query results from Google BigQuery. (Query: {sql_query})")
    
            raise
    
        else:
            logger.info(f"Query results fetched successfully. (Query: {sql_query})")
    
            return df

    def load_data(self, data: DataFrame, dataset: str, tablename:str , if_exists:str) -> None:
        """
        Load data table into Google BigQuery.
    
        Args:
            data (DataFrame): The dataframe containing the data that needs to be loaded.
            dataset (str): The name of the dataset that it needs to be loaded into.
            tablename (str): The name of the table that it needs to be loaded into.
            if_exists (str): Decides how to laod data if the table already exists.
        """
    
        try:
            table = dataset + "." + tablename
            pandas_gbq.to_gbq(
                data,
                table,
                project_id=self.project_id,
                if_exists=if_exists,
                credentials=self.credentials,
            )
    
        except:
            logger.exception(f"Couldn't load data into Google BigQuery table: {table}.")
    
            raise
    
        else:
            logger.info(f"Data loaded successfully into Google BigQuery table: {table}")