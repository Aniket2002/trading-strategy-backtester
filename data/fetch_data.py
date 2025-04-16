import os
import sys
import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker: str, start: str, end: str, save_path: str = "data"):
    """
    Downloads historical stock data using yfinance and saves it as a CSV.

    Args:
        ticker (str): Stock symbol (e.g., 'AAPL').
        start (str): Start date in 'YYYY-MM-DD'.
        end (str): End date in 'YYYY-MM-DD'.
        save_path (str): Folder where CSV will be saved.
    """
    print(f"Fetching data for {ticker} from {start} to {end}...")
    df = yf.download(ticker, start=start, end=end)

    if df.empty:
        print(f"⚠️ No data found for {ticker}.")
        return

    os.makedirs(save_path, exist_ok=True)
    file_path = os.path.join(save_path, f"{ticker.upper()}.csv")
    df.to_csv(file_path)
    print(f"✅ Data saved to {file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python fetch_data.py <TICKER> <START_DATE> <END_DATE>")
        print("Example: python fetch_data.py AAPL 2018-01-01 2023-12-31")
        sys.exit(1)

    ticker_arg = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]

    fetch_stock_data(ticker_arg, start_date, end_date)
