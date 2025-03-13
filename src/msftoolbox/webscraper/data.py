"""
data.py

This module defines the SeleniumScraperClient, a generic Selenium tool for extracting HTML table data from any website.
It provides methods to:
  - List all tables on a given webpage.
  - Scrape a selected table by index, with optional pagination support.

Example:
    >>> from data import SeleniumScraperClient
    >>> client = SeleniumScraperClient(headless=True)
    >>> tables = client.list_tables("https://example.com")
    >>> # Inspect the list to choose a table (e.g., index 0)
    >>> df = client.scrape_table_by_index(
    ...     "https://example.com", table_index=0, paginated=True,
    ...     next_button_xpath="//button[contains(., 'Next')]"
    ... )
"""

import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)


class SeleniumScraperClient:
    """
    A generic Selenium scraper client for extracting table data from web pages.

    This client provides methods to:
      - List all tables on a given webpage.
      - Scrape a chosen table by its index with optional pagination support.
    """

    def __init__(self, driver_path: str = None, headless: bool = True, implicit_wait: int = 10):
        """
        Initialize the SeleniumScraperClient.

        :param driver_path: Optional; path to the Selenium WebDriver executable. If None, ChromeDriverManager is used.
        :param headless: Optional; whether to run the browser in headless mode.
        :param implicit_wait: Optional; implicit wait time (in seconds) for Selenium.
        """
        self.driver_path = driver_path
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.driver = None

    def _init_driver(self):
        """
        Initialize the Selenium WebDriver.

        :raises Exception: If the driver initialization fails.
        """
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        try:
            if self.driver_path:
                service = Service(self.driver_path)
            else:
                service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(self.implicit_wait)
        except Exception as e:
            logging.error("Failed to initialize WebDriver: %s", e)
            raise

    def _quit_driver(self):
        """
        Quit the Selenium WebDriver if it is running.
        """
        if self.driver:
            self.driver.quit()
            self.driver = None

    def list_tables(self, url: str, table_selector: str = "table") -> list:
        """
        List all tables on the given webpage.

        :param url: URL of the webpage to inspect.
        :param table_selector: CSS selector to locate table elements. Defaults to "table".
        :return: A list of dictionaries, each with the table index, number of rows, number of columns,
                 and the raw Selenium element.
        :raises Exception: If the page cannot be loaded or no tables are found.
        """
        try:
            self._init_driver()
            self.driver.get(url)
            tables = self.driver.find_elements(By.CSS_SELECTOR, table_selector)
            if not tables:
                raise Exception("No tables found on the page.")
            tables_info = []
            for idx, table in enumerate(tables):
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    num_rows = len(rows)
                    num_columns = 0
                    if num_rows > 0:
                        header = rows[0].find_elements(By.TAG_NAME, "th")
                        if header:
                            num_columns = len(header)
                        else:
                            cells = rows[0].find_elements(By.TAG_NAME, "td")
                            num_columns = len(cells)
                    tables_info.append({
                        "index": idx,
                        "num_rows": num_rows,
                        "num_columns": num_columns,
                        "element": table
                    })
                except Exception as e:
                    logging.warning("Failed to extract info for table %d: %s", idx, e)
            return tables_info
        finally:
            self._quit_driver()

    def _extract_table(self, table_element) -> pd.DataFrame:
        """
        Extract data from a given table element into a pandas DataFrame.

        :param table_element: Selenium WebElement representing a table.
        :return: A pandas DataFrame containing the table data.
        """
        rows = table_element.find_elements(By.TAG_NAME, "tr")
        data = []
        headers = []
        for idx, row in enumerate(rows):
            th_elements = row.find_elements(By.TAG_NAME, "th")
            if th_elements and idx == 0:
                headers = [th.text.strip() for th in th_elements]
                continue
            td_elements = row.find_elements(By.TAG_NAME, "td")
            if td_elements:
                row_data = [td.text.strip() for td in td_elements]
                data.append(row_data)
        if headers and all(len(row) == len(headers) for row in data):
            return pd.DataFrame(data, columns=headers)
        else:
            return pd.DataFrame(data)

    def scrape_table_by_index(self, url: str, table_index: int = 0, table_selector: str = "table",
                              paginated: bool = False, next_button_xpath: str = None,
                              sleep_time: int = 2) -> pd.DataFrame:
        """
        Scrape a specific table by its index from the given URL.

        If the table is paginated, the method will click the "Next" button repeatedly,
        appending data from subsequent pages until pagination ends.

        :param url: URL of the webpage containing the table.
        :param table_index: Zero-based index of the table to scrape.
        :param table_selector: CSS selector to locate table elements. Defaults to "table".
        :param paginated: Boolean flag indicating if the table is paginated.
        :param next_button_xpath: XPath to locate the "Next" button (required if paginated is True).
        :param sleep_time: Time (in seconds) to pause after clicking the "Next" button.
        :return: A pandas DataFrame with the scraped table data.
        :raises Exception: If the specified table is not found or scraping fails.
        """
        try:
            self._init_driver()
            self.driver.get(url)
            wait = WebDriverWait(self.driver, self.implicit_wait)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, table_selector)))
            tables = self.driver.find_elements(By.CSS_SELECTOR, table_selector)
            if table_index < 0 or table_index >= len(tables):
                raise Exception(f"Table index {table_index} is out of range. Found {len(tables)} tables.")
            target_table = tables[table_index]
            all_data = []
            # Extract data from the initial table.
            df_initial = self._extract_table(target_table)
            headers = df_initial.columns.tolist()
            all_data.extend(df_initial.values.tolist())

            if paginated:
                if not next_button_xpath:
                    raise Exception("Next button XPath must be provided for paginated tables.")
                while True:
                    try:
                        next_button = self.driver.find_element(By.XPATH, next_button_xpath)
                        if not next_button.is_enabled() or 'disabled' in next_button.get_attribute("class"):
                            logging.info("Next button disabled. End of pagination reached.")
                            break
                        next_button.click()
                        time.sleep(sleep_time)
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, table_selector)))
                        tables = self.driver.find_elements(By.CSS_SELECTOR, table_selector)
                        if table_index >= len(tables):
                            logging.warning("Table index no longer available after pagination. Stopping.")
                            break
                        target_table = tables[table_index]
                        df_new = self._extract_table(target_table)
                        # Avoid duplicating header row if present.
                        new_data = df_new.values.tolist()
                        if new_data and new_data[0] == headers:
                            new_data = new_data[1:]
                        all_data.extend(new_data)
                    except Exception as e:
                        logging.info("No further pagination found: %s", e)
                        break

            # Construct the final DataFrame.
            if headers and all(len(row) == len(headers) for row in all_data):
                return pd.DataFrame(all_data, columns=headers)
            else:
                return pd.DataFrame(all_data)
        finally:
            self._quit_driver()


# Unit tests for SeleniumScraperClient can be added in a separate file (e.g., test_data.py)
if __name__ == "__main__":
    # Basic example usage:
    test_url = "https://foreignassistance.gov/cd/afghanistan/"  # Replace with an actual URL for testing

    client = SeleniumScraperClient(headless=True)

    # List tables on the page.
    try:
        tables_info = client.list_tables(test_url)
        print("Tables found on the page:")
        for table in tables_info:
            print(f"Index: {table['index']}, Rows: {table['num_rows']}, Columns: {table['num_columns']}")
    except Exception as err:
        print(f"Error listing tables: {err}")

    # Scrape a table by index.
    try:
        # Example: scrape the first table; set paginated=True if the table requires pagination.
        df_table = client.scrape_table_by_index(
            test_url, table_index=0, paginated=True
        )
        print("\nScraped Table DataFrame (first 5 rows):")
        print(df_table.head())
    except Exception as err:
        print(f"Error scraping table: {err}")
