import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def filter_country_year(df: pd.DataFrame, country: str, year: int = None) -> pd.DataFrame:
    """
    Filter the DataFrame for a specific country and fiscal year(s).

    If no year is provided, the function filters data for the last five fiscal years
    available for that country.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by (matches the "Country Name" column).
    :param year: Optional; a specific fiscal year to filter by.
    :return: A filtered DataFrame.
    """
    df_filtered = df[df["Country Name"] == country]
    if year is None:
        max_year = df_filtered["Fiscal Year"].max()
        years = list(range(max_year - 4, max_year + 1))
        df_filtered = df_filtered[df_filtered["Fiscal Year"].isin(years)]
    else:
        df_filtered = df_filtered[df_filtered["Fiscal Year"] == year]
    return df_filtered


def get_top_activities_by_funding(df: pd.DataFrame, country: str, year: int = None, top_n: int = 10) -> pd.DataFrame:
    """
    Get the top activities by current funding for a given country and fiscal year(s).

    Groups the data by "Activity Name" and sums the "Current Dollar Amount", then returns
    the top N entries sorted in descending order.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by.
    :param year: Optional; if provided, only include data for that fiscal year.
                 Otherwise, data from the last five fiscal years is used.
    :param top_n: The number of top activities to return.
    :return: A DataFrame with Activity Name and total current funding.
    """
    filtered = filter_country_year(df, country, year)
    summary = (
        filtered.groupby("Activity Name")["Current Dollar Amount"]
        .sum()
        .reset_index()
        .sort_values(by="Current Dollar Amount", ascending=False)
        .head(top_n)
    )
    return summary


def get_top_partners_by_funding(df: pd.DataFrame, country: str, year: int = None, top_n: int = 10) -> pd.DataFrame:
    """
    Get the top implementing partners by current funding for a given country and fiscal year(s).

    Groups the data by "Implementing Partner Name" and sums the "Current Dollar Amount",
    then returns the top N entries sorted in descending order.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by.
    :param year: Optional; if provided, only include data for that fiscal year.
                 Otherwise, data from the last five fiscal years is used.
    :param top_n: The number of top partners to return.
    :return: A DataFrame with Implementing Partner Name and total current funding.
    """
    filtered = filter_country_year(df, country, year)
    summary = (
        filtered.groupby("Implementing Partner Name")["Current Dollar Amount"]
        .sum()
        .reset_index()
        .sort_values(by="Current Dollar Amount", ascending=False)
        .head(top_n)
    )
    return summary


def get_top_sectors_by_funding(df: pd.DataFrame, country: str, year: int = None, top_n: int = 10) -> pd.DataFrame:
    """
    Get the top international sectors by current funding for a given country and fiscal year(s).

    Groups the data by "International Sector Name" and sums the "Current Dollar Amount",
    then returns the top N entries sorted in descending order.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by.
    :param year: Optional; if provided, only include data for that fiscal year.
                 Otherwise, data from the last five fiscal years is used.
    :param top_n: The number of top sectors to return.
    :return: A DataFrame with International Sector Name and total current funding.
    """
    filtered = filter_country_year(df, country, year)
    summary = (
        filtered.groupby("International Sector Name")["Current Dollar Amount"]
        .sum()
        .reset_index()
        .sort_values(by="Current Dollar Amount", ascending=False)
        .head(top_n)
    )
    return summary


def get_funding_per_category(df: pd.DataFrame, country: str, year: int = None) -> pd.DataFrame:
    """
    Summarize current funding per US category for a given country and fiscal year(s).

    Groups the data by "US Category Name" and sums the "Current Dollar Amount",
    then sorts the results in descending order.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by.
    :param year: Optional; if provided, only include data for that fiscal year.
                 Otherwise, data from the last five fiscal years is used.
    :return: A DataFrame with US Category Name and total current funding.
    """
    filtered = filter_country_year(df, country, year)
    summary = (
        filtered.groupby("US Category Name")["Current Dollar Amount"]
        .sum()
        .reset_index()
        .sort_values(by="Current Dollar Amount", ascending=False)
    )
    return summary


# ------------------------- Plotting Functions ------------------------- #

def plot_top_activities_by_funding(df: pd.DataFrame, country: str, year: int = None, top_n: int = 10) -> None:
    """
    Plot the top activities by current funding for a given country and fiscal year(s).

    Creates a horizontal bar chart of the top N activities.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by.
    :param year: Optional; a specific fiscal year. If not provided, uses the last five years.
    :param top_n: The number of top activities to display.
    """
    summary = get_top_activities_by_funding(df, country, year, top_n)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=summary, x="Current Dollar Amount", y="Activity Name", orient="h")
    plt.title(f"Top {top_n} Activities by Funding in {country}" +
              (f" for {year}" if year else " (Last 5 Years)"))
    plt.xlabel("Current Funding (Dollars)")
    plt.ylabel("Activity")
    plt.tight_layout()
    plt.show()


def plot_top_partners_by_funding(df: pd.DataFrame, country: str, year: int = None, top_n: int = 10) -> None:
    """
    Plot the top implementing partners by current funding for a given country and fiscal year(s).

    Creates a horizontal bar chart of the top N partners.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by.
    :param year: Optional; a specific fiscal year. If not provided, uses the last five years.
    :param top_n: The number of top partners to display.
    """
    summary = get_top_partners_by_funding(df, country, year, top_n)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=summary, x="Current Dollar Amount", y="Implementing Partner Name", orient="h")
    plt.title(f"Top {top_n} Partners by Funding in {country}" +
              (f" for {year}" if year else " (Last 5 Years)"))
    plt.xlabel("Current Funding (Dollars)")
    plt.ylabel("Partner")
    plt.tight_layout()
    plt.show()


def plot_top_sectors_by_funding(df: pd.DataFrame, country: str, year: int = None, top_n: int = 10) -> None:
    """
    Plot the top international sectors by current funding for a given country and fiscal year(s).

    Creates a horizontal bar chart of the top N sectors.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by.
    :param year: Optional; a specific fiscal year. If not provided, uses the last five years.
    :param top_n: The number of top sectors to display.
    """
    summary = get_top_sectors_by_funding(df, country, year, top_n)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=summary, x="Current Dollar Amount", y="International Sector Name", orient="h")
    plt.title(f"Top {top_n} Sectors by Funding in {country}" +
              (f" for {year}" if year else " (Last 5 Years)"))
    plt.xlabel("Current Funding (Dollars)")
    plt.ylabel("Sector")
    plt.tight_layout()
    plt.show()


def plot_funding_per_category(df: pd.DataFrame, country: str, year: int = None) -> None:
    """
    Plot current funding per US category for a given country and fiscal year(s).

    Creates a horizontal bar chart that shows total funding per category.

    :param df: The DataFrame containing funding data.
    :param country: The country name to filter by.
    :param year: Optional; a specific fiscal year. If not provided, uses the last five years.
    """
    summary = get_funding_per_category(df, country, year)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=summary, x="Current Dollar Amount", y="US Category Name", orient="h")
    plt.title(f"Funding per Category in {country}" +
              (f" for {year}" if year else " (Last 5 Years)"))
    plt.xlabel("Current Funding (Dollars)")
    plt.ylabel("US Category")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Example usage:
    # Ensure that your DataFrame 'df' is loaded before using these functions.
    #
    # For instance:
    # df = pd.read_csv("https://s3.amazonaws.com/files.explorer.devtechlab.com/us_foreign_aid_complete.csv")
    #
    # Then call any of the functions below:

    # country = "Afghanistan"
    # year = 2010  # Or set to None for the last 5 years
    # print(get_top_activities_by_funding(df, country, year))
    # plot_top_activities_by_funding(df, country, year)

    # Similarly, test other functions as needed.
    pass
