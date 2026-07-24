from interfaces import ApiPriceFetcher
import requests
from os import environ
from logging import getLogger

logger = getLogger(__name__)

class TiingoApiFetcher(ApiPriceFetcher):

    def __init__(self, token: str = environ.get("tiingo_api_token")):
        self.token = "Token " + token
        self.headers ={
                            "Content-Type": "application/json",
                            "Authorization": self.token,
                        }


    @property
    def timeout(self) -> int:

        return 10

    def get_prices(self, identifier_list: list) -> list:
        """
        Fetch the ticker prices from the Tiingo API.
    
        Args:
            identifier_list (list): Containing the tickers that we need prices for.

        Returns:
            list: Containing the date of the price, the ticker and the price for that ticker.
        """

        try:
            price_list = []
            # Iterating because Tiingo only supports singular ticker requests.
            for ticker in identifier_list:
    
                response = requests.get(
                    f"https://api.tiingo.com/tiingo/daily/{ticker}/prices",
                    headers=self.headers,
                    timeout=self.timeout,
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
    
        except:
            logger.exception("Couldn't fetch API asset prices.")
    
            raise
    
        else:
            logger.info("API asset prices fetched successfully.")
    
            return price_list

    def get_metadata(self, asset_tickers: list):

        """
        Fetch the ticker metadata from the Tiingo API.
    
        Args:
            asset_tickers (list): Containing the tickers that we need metadata for.
            conf (dict): The dict containing the configurating data and authentications.
    
        Returns:
            list: Containing the ticker, the full name of the assets and the exchange code it is traded on.
        """
    
        try:
            metadata_list = []
            # Iterating because Tiingo only supports singular ticker requests.
            for ticker in asset_tickers:
    
                response = requests.get(
                    f"https://api.tiingo.com/tiingo/daily/{ticker}",
                    headers=self.headers,
                    timeout=10,
                )
    
                r = response.json()
                if r["name"] and r["exchangeCode"]:
                    metadata = {
                        "tickers": ticker,
                        "asset_name": r["name"],
                        "exchange_code": r["exchangeCode"],
                    }
                    metadata_list.append(metadata)
                
                else:
                    logger.warning(f"{ticker} metadata was not found by Tiingo API.")
    
        except:
            logger.exception("Couldn't fetch API asset metadata.")
    
            raise
    
        else:
            logger.info("API asset metadata fetched successfully.")
    
            return metadata_list

