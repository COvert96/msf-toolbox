import time
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)


class DataScraperClient:
    """
    A reusable client for scraping paginated tables from websites and reading CSV data from URLs.

    This client uses Selenium to navigate paginated tables and load their data into a pandas DataFrame.
    It also provides a static method to load CSV data directly into a DataFrame.

    :Example:

    >>> client = DataScraperClient(headless=True)
    >>> df_table = client.scrape_paginated_table("https://example.com/table_page")
    >>> df_csv = DataScraperClient.read_csv_from_url("https://s3.amazonaws.com/files.explorer.devtechlab.com/us_foreign_aid_complete.csv")
    """

    def __init__(self, driver_path: str = None, headless: bool = True, implicit_wait: int = 10):
        """
        Initialize the DataScraperClient.

        :param driver_path: Path to the Selenium WebDriver executable. If None, the driver is assumed to be in PATH.
        :param headless: Whether to run the browser in headless mode.
        :param implicit_wait: The implicit wait time (in seconds) for Selenium.
        """
        self.driver_path = driver_path
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.driver = None

    def _init_driver(self):
        """
        Initialize the Selenium WebDriver.
        """
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        # If driver_path is provided, use it; otherwise, assume driver is in PATH.
        if self.driver_path:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(self.implicit_wait)

    def _quit_driver(self):
        """
        Quit the Selenium WebDriver if it is running.
        """
        if self.driver:
            self.driver.quit()
            self.driver = None

    def scrape_paginated_table(self, url: str, table_selector: str = "table.usa-table",
                               next_button_xpath: str = "//button[contains(., 'next page')]",
                               sleep_time: int = 2) -> pd.DataFrame:
        """
        Scrape a paginated table from the specified URL and return its data as a pandas DataFrame.

        :param url: URL of the webpage containing the paginated table.
        :param table_selector: CSS selector to locate the table element.
        :param next_button_xpath: XPath expression to locate the 'Next' button for pagination.
        :param sleep_time: Time (in seconds) to pause after clicking the next button.
        :return: A pandas DataFrame with the scraped table data.
        :raises Exception: If the table cannot be found or scraping fails.
        """
        try:
            self._init_driver()
            self.driver.get(url)
            wait = WebDriverWait(self.driver, self.implicit_wait)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, table_selector)))

            all_data = []
            headers = []

            # Attempt to extract table headers
            try:
                table = self.driver.find_element(By.CSS_SELECTOR, table_selector)
                header_elements = table.find_elements(By.TAG_NAME, "th")
                if header_elements:
                    headers = [header.text.strip() for header in header_elements]
            except Exception:
                logging.warning("Unable to extract table headers.")

            # Loop through all pages
            while True:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, table_selector)))
                table = self.driver.find_element(By.CSS_SELECTOR, table_selector)
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if cells:
                        row_data = [cell.text.strip() for cell in cells]
                        all_data.append(row_data)

                # Try to click the 'Next' button
                try:
                    next_button = self.driver.find_element(By.XPATH, next_button_xpath)
                    if not next_button.is_enabled() or 'disabled' in next_button.get_attribute("class"):
                        logging.info("Next button disabled. End of pagination.")
                        break
                    next_button.click()
                    time.sleep(sleep_time)
                except Exception:
                    logging.info("No next button found. Assuming last page reached.")
                    break

            # Create DataFrame using headers if they match the data rows
            if headers and all(len(row) == len(headers) for row in all_data):
                df = pd.DataFrame(all_data, columns=headers)
            else:
                df = pd.DataFrame(all_data)
            return df
        finally:
            self._quit_driver()

    @staticmethod
    def read_csv_from_url(csv_url: str) -> pd.DataFrame:
        """
        Read CSV data from the provided URL into a pandas DataFrame.

        :param csv_url: URL of the CSV file.
        :return: A pandas DataFrame containing the CSV data.
        :raises Exception: If reading the CSV fails.
        """
        # Define dtype map (force string types for mixed-type columns)
        dtype_map = {
            6: str,  # Income Group ID
            7: str,  # Income Group Name
            12: str,  # Managing Sub-agency or Bureau ID
        }

        # Load CSV with dtype enforcement for non-integer columns, handling potential parsing issues
        df = pd.read_csv(csv_url, dtype=dtype_map, low_memory=False)

        # Clean column 48 (Fiscal Year) by extracting valid 4-digit years
        df.iloc[:, 48] = pd.to_numeric(
            df.iloc[:, 48].astype(str).str.extract(r'(\d{4})')[0],
            errors='coerce'
        ).astype('Int64')  # Use nullable integer type

        # Handle missing or invalid values
        logging.log(20,
                    f"Column 48 (Fiscal Year): {df.iloc[:, 48].isna().sum()} rows had invalid year values and were "
                    f"set to NaN.")

        # Convert other numeric columns safely (if needed, add more columns here)
        numeric_columns = [48]  # Add other numeric columns if required
        for col in numeric_columns:
            df.iloc[:, col] = pd.to_numeric(df.iloc[:, col], errors='coerce').astype('Int64')

        return df


if __name__ == "__main__":
    # Example usage for scraping a paginated table
    paginated_url = "https://example.com/paginated_table_page"  # Replace with the actual URL
    client = DataScraperClient(headless=True)
    try:
        df_table = client.scrape_paginated_table(paginated_url)
        print("Paginated Table Data (first 5 rows):")
        print(df_table.head())
    except Exception as e:
        print(f"Error scraping paginated table: {e}")

    # Example usage for reading CSV data
    csv_url = "https://s3.amazonaws.com/files.explorer.devtechlab.com/us_foreign_aid_complete.csv"
    try:
        df_csv = DataScraperClient.read_csv_from_url(csv_url)
        print("\nCSV Data (first 5 rows):")
        print(df_csv.head())
    except Exception as e:
        print(f"Error reading CSV data: {e}")
