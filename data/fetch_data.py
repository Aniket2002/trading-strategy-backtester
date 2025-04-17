import os
import sys
import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker: str, start: str, end: str, save_path: str = "data"):
    print(f"📡 Fetching {ticker} from {start} to {end}...")

    df = yf.download(ticker, start=start, end=end)

    if df.empty:
        print(f"⚠️ No data found for {ticker}")
        return

    # Drop unnecessary columns
    df.drop(columns=["Adj Close"], errors="ignore", inplace=True)

    # Ensure the output folder exists
    os.makedirs(save_path, exist_ok=True)
    file_path = os.path.join(save_path, f"{ticker.upper()}.csv")

    # Save initial file
    df.to_csv(file_path, index=True)

    # 🧹 Extra: Clean the file if corruption like 'Ticker' or 'Price' detected
    with open(file_path, "r") as f:
        first_line = f.readline().strip()
        if first_line.startswith("Price") or "Ticker" in f.readline():
            print("⚠️ Detected malformed header, cleaning...")
            fix_corrupted_csv(file_path)

    print(f"✅ Clean data saved to {file_path}")

def fix_corrupted_csv(file_path: str):
    df_raw = pd.read_csv(file_path, header=None)
    df_clean = df_raw.iloc[3:].reset_index(drop=True)
    df_clean.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df_clean.to_csv(file_path, index=False)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python fetch_data.py <TICKER> <START_DATE> <END_DATE>")
        sys.exit(1)

    ticker_arg = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]

    fetch_stock_data(ticker_arg, start_date, end_date)
