import pandas as pd
import numpy as np
import os

def simulate_trading(df: pd.DataFrame, initial_cash: float = 100000.0, save_reports: bool = True) -> pd.DataFrame:
    """
    Simulates a simple long-only strategy and tracks performance.
    Includes full debugging for Position values.
    """
    df = df.copy()

    cash = initial_cash
    holdings = 0
    portfolio_values = []
    trades = []

    for idx, row in df.iterrows():
        price = row["Close"]
        signal = ""
        shares = 0

        # ✅ Debug: Check Position type and value
        try:
            position_raw = row["Position"]
            print(f"[DEBUG] {idx} - Position raw type: {type(position_raw)}, value: {position_raw}")

            # Convert to float if it's not already
            if isinstance(position_raw, pd.Series):
                position = float(position_raw.iloc[0])
            else:
                position = float(position_raw)

        except Exception as e:
            print(f"[ERROR] {idx} - Could not convert Position: {row['Position']} → {e}")
            position = 0.0

        # ✅ Buy logic
        if position == 1.0 and cash > 0:
            shares = cash / price
            holdings = shares
            cash = 0
            signal = "BUY"
            trades.append((idx, signal, price, shares))

        # ✅ Sell logic
        elif position == -1.0 and holdings > 0:
            cash = holdings * price
            shares = holdings
            holdings = 0
            signal = "SELL"
            trades.append((idx, signal, price, shares))

        total_value = cash + (holdings * price)
        portfolio_values.append([cash, holdings * price, total_value, signal])

    df["Cash"], df["Holdings"], df["Total Value"], df["Buy/Sell"] = zip(*portfolio_values)

    if save_reports:
        os.makedirs("reports", exist_ok=True)
        trade_log_df = pd.DataFrame(trades, columns=["Date", "Action", "Price", "Shares"])
        trade_log_df.to_csv("reports/trade_log.csv", index=False)
        returns = df["Total Value"].pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        max_dd = (df["Total Value"] / df["Total Value"].cummax() - 1).min()
        summary = {
            "Initial Capital": initial_cash,
            "Final Portfolio Value": round(df["Total Value"].iloc[-1], 2),
            "Total Return (%)": round((df["Total Value"].iloc[-1] / initial_cash - 1) * 100, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown": round(max_dd * 100, 2),
            "Total Trades": len(trade_log_df)
        }
        pd.DataFrame([summary]).to_csv("reports/strategy_summary.csv", index=False)

    return df
