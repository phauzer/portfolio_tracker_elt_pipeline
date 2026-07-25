from abc import ABC, abstractmethod

class ApiPriceFetcher(ABC):

    @property
    @abstractmethod
    def timeout(self) -> int:
        pass

    @abstractmethod
    def get_prices(self, identifier_list: list) -> list:
        pass