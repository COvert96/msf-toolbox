# WebScraper Module

This repository provides two distinct scraping clients to handle different scenarios:

1. **SeleniumScraperClient** (in `dynamic.py`): Ideal for scraping data from dynamically loaded or JavaScript-heavy pages.
2. **BeautifulSoupScraperClient** (in `static.py`): Great for simpler, static websites where the table data is already rendered in the HTML source.

## 1. SeleniumScraperClient

### Overview

`SeleniumScraperClient` leverages Selenium to scrape data from webpages that require JavaScript execution or dynamic interactions. It offers methods for:
- Listing tables on a page, including row and column counts
- Extracting data from a chosen table by index
- Optionally following pagination using a “Next” button or similar UI element
- Logging and clear exception messages

### Features

- **List Tables**: Retrieves a list of all tables, including row/column counts.
- **Scrape Tables**: Extracts data into a `pandas.DataFrame`.
- **Optional Pagination**: Click a “Next” button (identified by XPath) until no more pages remain.
- **Error Handling**: Handles initialization errors, invalid table indexes, missing pagination controls, etc.

### Usage

#### Installation/Setup
```bash
pip install selenium webdriver-manager pandas
```

#### Initialization
```python
from dynamic import SeleniumScraperClient

# Initialize the scraper client
client = SeleniumScraperClient(
    headless=True,      # Run the browser in headless mode
    implicit_wait=10    # Implicit wait time in seconds
)
```

#### List Tables
```python
tables_info = client.list_tables("https://example.com")
for table_info in tables_info:
    print(table_info)  # Each entry includes the table index, row/col counts, and the raw WebElement
```

#### Scrape Table by Index
```python
df = client.scrape_table_by_index(
    url="https://example.com",
    table_index=0,
    paginated=True,
    next_button_xpath="//button[contains(., 'next page')]"
)
print(df.head())
```

#### Example Workflow
```python
# 1. Initialize the client
client = SeleniumScraperClient(headless=True)

# 2. List tables on the page
tables_info = client.list_tables("https://example.com")

# Pick a table index from the above list
chosen_index = 0

# 3. Scrape the chosen table
df_table = client.scrape_table_by_index(
    url="https://example.com",
    table_index=chosen_index,
    paginated=True,
    next_button_xpath="//button[contains(., 'next page')]"
)

# 4. Inspect the data
print(df_table.head())
```

---

## 2. BeautifulSoupScraperClient

### Overview

`BeautifulSoupScraperClient` uses Requests and BeautifulSoup to scrape data from **static** pages (i.e., HTML is directly rendered without needing JavaScript). If you don’t need JavaScript execution or button-click pagination, this client is significantly simpler and faster than Selenium.

### Features

- **List Tables**: Finds all `<table>` elements, including row and column stats.
- **Scrape Tables**: Converts table data into a `pandas.DataFrame`.
- **Optional Pagination**: Follows an `<a>` link or similar “Next” link to load subsequent pages.
- **Fewer Dependencies**: Relies on `requests` and `beautifulsoup4` only.

### Usage

#### Installation/Setup
```bash
pip install requests beautifulsoup4 pandas
```

#### Initialization
```python
from static import BeautifulSoupScraperClient

# Initialize the scraper client
client = BeautifulSoupScraperClient(
    timeout=10  # HTTP request timeout in seconds
)
```

#### List Tables
```python
tables_info = client.list_tables("https://example.com")
for table_info in tables_info:
    print(table_info)  # Includes the table index, row/col counts, and the raw BeautifulSoup element
```

#### Scrape Table by Index
```python
df = client.scrape_table_by_index(
    url="https://example.com",
    table_index=0,
    paginated=True,
    next_button_selector="a.next",  # or other link CSS selector
    sleep_time=2                    # optional pause between page requests
)
print(df.head())
```

#### Example Workflow
```python
# 1. Initialize the client
client = BeautifulSoupScraperClient()

# 2. List tables on the page
tables_info = client.list_tables("https://example.com")

# Pick a table index from the above list
chosen_index = 0

# 3. Scrape the chosen table
df_table = client.scrape_table_by_index(
    url="https://example.com",
    table_index=chosen_index,
    paginated=True,
    next_button_selector="a.next"
)

# 4. Inspect the data
print(df_table.head())
```

---

## Choosing Which Client to Use

- **Dynamic Content**: If the site relies heavily on JavaScript or only loads table data after certain interactions (clicking, infinite scroll, etc.), use **SeleniumScraperClient** in `dynamic.py`.
- **Static Content**: If the data is present in the initial HTML (no JavaScript needed), use **BeautifulSoupScraperClient** in `static.py`.

---

## Error Handling and Logging

Both clients log errors and raise exceptions when:
- A requested table index doesn’t exist
- Pagination is enabled but pagination controls aren’t provided
- Network or driver initialization fails

This helps ensure you know exactly what went wrong and where.

---

## License

Use and modify these scraper clients at your own discretion. They’re provided as-is, without warranty or guarantee. Always remember to scrape responsibly and follow the target site’s Terms of Service. 
