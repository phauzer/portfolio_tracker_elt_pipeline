import gspread
from os import environ
from logging import getLogger

logger = getLogger(__name__)

class GoogleSheetApi:

    def __init__(self, service_account_filename: str = environ.get("gc_service_account_json_path"), sheet_name:str = "portfolio_transactions", worksheet_name: str = "Transactions") -> None:

        self.service_account = service_account_filename
        self.sheet_name = sheet_name
        self.worksheet_name = worksheet_name
        self.status = "Pending"

        try:
            self.gc = gspread.service_account(filename=self.service_account)
            self.sh = self.gc.open(self.sheet_name)
            self.worksheet = self.sh.worksheet(self.worksheet_name)

        except:
            logger.exception("Couldn't establish connection to Google Sheet.")

    def extract(self) -> list:
        """
        Fetch the batch of data from Google Sheets.
    
        Returns:
            list: Contains the data, if no data were extracted, it returns an empty list.
        """

        try:
            transaction_list = self.worksheet.get_all_records()

        except:
            logger.exception("Couldn't read transactions from google sheets.")

        else:
            if not transaction_list:
                logger.info("The transactions sheet was empty.")
    
            else:
                logger.info("Transactions read successfully.")
                self.status = "Extracted"
    
            return transaction_list

    def make_worksheet(self, name: str, rows: int, cols: int) -> None:
        """
        Makes a worksheet in the given spreadsheet.

        Args:
            name (str): Name of the desired sheet.
            rows (int): The amount of rows the sheet should have.
            cols (int): The amount of columns the sheet should have.
        """
        worksheet_list = self.sh.worksheets()
        worksheet_names = [ws.title for ws in worksheet_list]
        if name in worksheet_names:
            logger.info(f"The {name} worksheet already exists")

        else:
            try:
                self.sh.add_worksheet(title=name, rows=rows, cols=cols)

            except:
                logger.exception(f"Couldn't create '{name}' worksheet.")

    def append_data(self, target_worksheet: str, data: list) -> None:
        """
        Appends a list of data to a worksheet.

        Args:
            target_worksheet (str): The name of the existing worksheet in the given spreadsheet.
            data (list): A list containing dicts for rows. Every dict has the head rows as keys and the given values as values.
        """

        if self.status == "Extracted":
            rows_to_append = [list(row.values()) for row in data]

            try:
                self.sh.values_append(target_worksheet, {'valueInputOption': 'USER_ENTERED'}, {'values': rows_to_append})

            except:
                logger.exception("Couldn't copy data to target sheet.")

            else:
                logger.info(f"Data appended into {target_worksheet}.")
                self.status = "Appended"

        else:
            logger.info(f"Couldn't append data, data were not extracted.")

    def sheet_cleanup(self, from_cell: str, to_cell: str) -> None:
        """
        Cleans the Google Sheet in the given parameters

        Args:
            from_cell (str): The first cell of the cells thats needed to be cleaned up.
            to_cell (str): The last cell of the cells thats needed to be cleaned up.
        """
    
        if self.status == "Appended":
            try:
                self.worksheet.batch_clear([from_cell+":"+to_cell])
    
            except:
                logger.exception("Couldn't clear Google Sheets from data")
    
            else:
                logger.info("Google Sheets cleaned successfully.")
                self.status = "Successful"
    
        else:
            logger.info(
                "Couldn't clear the sheet, data were not yet archived"
            )