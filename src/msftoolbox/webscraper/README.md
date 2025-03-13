# SeleniumScraperClient

## Overview

`SeleniumScraperClient` is a Python class designed for scraping data from websites using Selenium. It provides methods for listing tables on a webpage, scraping table data (including paginated tables), and returning results in a structured format (pandas DataFrame) for further analysis or storage.

## Features

- **List Tables**: Retrieve a list of all tables on a page, including row and column counts.
- **Scrape Tables**: Extract data from a chosen table by its index.
- **Optional Pagination**: Navigate to additional pages of data when a "Next" button (or similar) is present.
- **Error Handling**: Manage errors gracefully, providing logs and clear messages.

## Usage

### Initialization

```python
from data import SeleniumScraperClient

# Initialize the scraper client
client = SeleniumScraperClient(
    headless=True,      # whether to run browser in headless mode
    implicit_wait=10    # implicit wait time (seconds) for Selenium
)
```

### Methods

#### List Tables
Retrieve a list of dictionaries describing each table found on the page. The dictionary includes:
- Index (zero-based index of the table on the page)
- Number of rows
- Number of columns
- Selenium WebElement reference

```python
tables_info = client.list_tables("https://example.com")
for table_info in tables_info:
    print(table_info)
```

#### Scrape Table by Index
Extract the data from a specific table by specifying its index. Optionally handle pagination by setting `paginated=True` and providing the XPath for the “Next” button.

```python
df = client.scrape_table_by_index(
    url="https://example.com",
    table_index=0,
    paginated=True,
    next_button_xpath="//button[contains(., 'next page')]"
)
```

### Example Workflow

Below is a simple workflow demonstrating how to list available tables on a page and then scrape one of them (with or without pagination).

```python
# Initialize the client
client = SeleniumScraperClient(headless=True)

# Step 1: List all tables on the webpage
tables_info = client.list_tables("https://example.com")

# Inspect the output and choose a table index (e.g., 0)
chosen_index = 0

# Step 2: Scrape the chosen table (assume it's paginated)
df_table = client.scrape_table_by_index(
    url="https://example.com",
    table_index=chosen_index,
    paginated=True,
    next_button_xpath="//button[contains(., 'next page')]"
)

# Step 3: Examine the DataFrame
print(df_table.head())
```

## Error Handling

- **Driver Initialization**: If the Selenium WebDriver fails to initialize, an error is logged and re-raised.
- **Table Not Found**: If a specified table index is out of range, an exception is raised with a clear message.
- **Pagination**: If a user sets `paginated=True` but does not provide a valid `next_button_xpath`, an exception is raised.
- **Exception Logging**: Any unexpected errors during table extraction or pagination are caught, logged, and clearly communicated.

This class provides a structured approach to extracting and processing data from websites, with built-in error handling to ensure reliable operation.
