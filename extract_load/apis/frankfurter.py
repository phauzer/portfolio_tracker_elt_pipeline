from apis.interfaces import ApiPriceFetcher
import requests
from logging import getLogger

logger = getLogger(__name__)

class FrankfurterFxFetcher(ApiPriceFetcher):

    @property
    def timeout(self):

         return 60

    def get_prices(self, identifier_list: list, base_currency: str = "EUR") -> list:
        """
        Fetch the currency rates from the Frankfurter API.
    
        Args:
            identifier_list (list): Containing the currencies that we need the rates for with EUR base.
    
        Returns:
            list: Containing the date of the exchange rate, the currency code and the rate for that currency with the given currency base(default: EUR).
        """

        try:
                # The Frankfurter API supports bulk requests, we dont need to iterate.
                currency_str = ",".join(identifier_list)
        
                response = requests.get(
                    f"https://api.frankfurter.dev/v2/rates?base={base_currency}&quotes={currency_str}", timeout=self.timeout
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
        
        except:
            logger.exception("Couldn't fetch API currency rates.")
    
            raise
    
        else:
            logger.info("API currency rates fetched successfully.")
    
            return currencies