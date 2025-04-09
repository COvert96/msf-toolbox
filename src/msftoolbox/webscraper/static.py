"""
data_bs.py

This module defines the BeautifulSoupScraperClient, a generic tool for extracting HTML table data
from any website using requests and BeautifulSoup. It provides methods to:
  - List all tables on a given webpage.
  - Scrape a selected table by index, with optional pagination support.

Note:
    This client works for static content. Dynamic pages that require JavaScript execution won't work.
    For paginated tables, the next page must be accessible via a standard link (i.e. the element must have an "href" attribute).

Example:
    >>> from data_bs import BeautifulSoupScraperClient
    >>> client = BeautifulSoupScraperClient()
    >>> tables = client.list_tables("https://example.com")
    >>> # Inspect tables to choose one (e.g., index 0)
    >>> df = client.scrape_table_by_index(
    ...     "https://example.com", table_index=0, paginated=True,
    ...     next_button_selector="a.next"
    ... )
"""

import time
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)


class BeautifulSoupScraperClient:
    """
    A generic scraper client for extracting table data using BeautifulSoup.

    Provides methods to:
      - List all tables on a webpage.
      - Scrape a chosen table by its index with optional pagination support.
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize the BeautifulSoupScraperClient.

        :param timeout: Optional; timeout for HTTP requests (in seconds).
        """
        self.timeout = timeout

    def list_tables(self, url: str, table_selector: str = "table") -> list:
        """
        List all tables on the given webpage.

        :param url: URL of the webpage to inspect.
        :param table_selector: CSS selector to locate table elements. Defaults to "table".
        :return: A list of dictionaries containing the table index, number of rows, number of columns,
                 and the raw BeautifulSoup element.
        :raises Exception: If the page cannot be loaded or no tables are found.
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except Exception as e:
            logging.error("Failed to retrieve URL %s: %s", url, e)
            raise

        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.select(table_selector)
        if not tables:
            raise Exception("No tables found on the page.")
        tables_info = []
        for idx, table in enumerate(tables):
            rows = table.find_all("tr")
            num_rows = len(rows)
            num_columns = 0
            if num_rows > 0:
                header = rows[0].find_all("th")
                if header:
                    num_columns = len(header)
                else:
                    cells = rows[0].find_all("td")
                    num_columns = len(cells)
            tables_info.append({
                "index": idx,
                "num_rows": num_rows,
                "num_columns": num_columns,
                "element": table
            })
        return tables_info

    def _extract_table(self, table_element) -> pd.DataFrame:
        """
        Extract data from a given table element into a pandas DataFrame.

        :param table_element: A BeautifulSoup element representing a table.
        :return: A pandas DataFrame containing the table data.
        """
        rows = table_element.find_all("tr")
        data = []
        headers = []
        for idx, row in enumerate(rows):
            th_elements = row.find_all("th")
            if th_elements and idx == 0:
                headers = [th.get_text(strip=True) for th in th_elements]
                continue
            td_elements = row.find_all("td")
            if td_elements:
                row_data = [td.get_text(strip=True) for td in td_elements]
                data.append(row_data)
        if headers and all(len(row) == len(headers) for row in data):
            return pd.DataFrame(data, columns=headers)
        else:
            return pd.DataFrame(data)

    def scrape_table_by_index(self, url: str, table_index: int = 0, table_selector: str = "table",
                                paginated: bool = False, next_button_selector: str = None,
                                sleep_time: int = 2) -> pd.DataFrame:
        """
        Scrape a specific table by its index from the given URL.

        If paginated is True, the method will follow the "next" link repeatedly,
        appending data from subsequent pages until no further pagination is detected.

        :param url: URL of the webpage containing the table.
        :param table_index: Zero-based index of the table to scrape.
        :param table_selector: CSS selector to locate table elements. Defaults to "table".
        :param paginated: Boolean flag indicating if the table is paginated.
        :param next_button_selector: CSS selector to locate the "Next" button. Required if paginated is True.
        :param sleep_time: Time (in seconds) to pause between requests.
        :return: A pandas DataFrame with the scraped table data.
        :raises Exception: If the specified table is not found or scraping fails.
        """
        if paginated and not next_button_selector:
            raise Exception("Next button CSS selector must be provided for paginated tables.")

        all_data = []
        headers = None
        current_url = url

        while True:
            try:
                response = requests.get(current_url, timeout=self.timeout)
                response.raise_for_status()
            except Exception as e:
                logging.error("Failed to retrieve URL %s: %s", current_url, e)
                break

            soup = BeautifulSoup(response.text, "html.parser")
            tables = soup.select(table_selector)
            if table_index < 0 or table_index >= len(tables):
                raise Exception(f"Table index {table_index} is out of range. Found {len(tables)} tables.")
            target_table = tables[table_index]
            df_table = self._extract_table(target_table)
            if headers is None and not df_table.empty:
                headers = df_table.columns.tolist()
            # Avoid duplicating header row if present in subsequent pages.
            if headers and list(df_table.columns) == headers:
                new_data = df_table.values.tolist()
            all_data.extend(new_data)

            if not paginated:
                break

            next_button = soup.select_one(next_button_selector)
            if not next_button or not next_button.get("href"):
                logging.info("No further pagination found. Ending pagination loop.")
                break

            next_url = urljoin(current_url, next_button.get("href"))
            if next_url == current_url:
                logging.info("Next page URL is the same as current page. Ending pagination loop.")
                break

            logging.info("Moving to next page: %s", next_url)
            current_url = next_url
            time.sleep(sleep_time)

        if headers and all(len(row) == len(headers) for row in all_data):
            return pd.DataFrame(all_data, columns=headers)
        else:
            return pd.DataFrame(all_data)


# Basic example usage:
if __name__ == "__main__":
    test_url = "https://fts.unocha.org/global-funding/donors/2025"  # Replace with an actual URL for testing

    client = BeautifulSoupScraperClient()

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
        # Example: scrape the first table; set paginated=True and provide next_button_selector if pagination is needed.
        df_table = client.scrape_table_by_index(
            test_url, table_index=0, paginated=False
        )
        print("\nScraped Table DataFrame (first 5 rows):")
        print(df_table.head())
    except Exception as err:
        print(f"Error scraping table: {err}")
