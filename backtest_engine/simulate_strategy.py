import pandas as pd
import numpy as np
import os

def simulate_trading(df: pd.DataFrame, initial_cash: float = 100000.0, save_reports: bool = True) -> pd.DataFrame:
    """
    Simulates a simple long-only strategy and tracks performance.

    Args:
        df (pd.DataFrame): Must contain 'Close' and 'Position' columns.
        initial_cash (float): Starting capital.
        save_reports (bool): Save logs and summary to reports/.

    Returns:
        pd.DataFrame: With portfolio tracking columns.
    """
    df = df.copy()

    cash = initial_cash
    holdings = 0
    portfolio_values = []
    trades = []

    for idx, row in df.iterrows():
        price = row["Close"]

        # SAFELY extract scalar position value
        try:
            val = row["Position"]
            if isinstance(val, pd.Series):
                position = float(val.iloc[0])
            else:
                position = float(val)
        except Exception as e:
            print(f"⚠️ Position error at {idx}: {e}")
            position = 0.0

        signal = ""
        shares = 0

        # BUY condition
        is_buy = position == 1.0
        if isinstance(is_buy, pd.Series):
            is_buy = is_buy.iloc[0]
        if is_buy and cash > 0:
            shares = cash / price
            holdings = shares
            cash = 0
            signal = "BUY"
            trades.append((idx, signal, price, shares))

        # SELL condition
        is_sell = position == -1.0
        if isinstance(is_sell, pd.Series):
            is_sell = is_sell.iloc[0]
        if is_sell and holdings > 0:
            cash = holdings * price
            shares = holdings
            holdings = 0
            signal = "SELL"
            trades.append((idx, signal, price, shares))


        total_value = cash + (holdings * price)
        portfolio_values.append([cash, holdings * price, total_value, signal])

    # Attach results to dataframe
    df["Cash"], df["Holdings"], df["Total Value"], df["Buy/Sell"] = zip(*portfolio_values)

    # Export reports if needed
    if save_reports:
        os.makedirs("reports", exist_ok=True)

        # Trade log
        trade_log_df = pd.DataFrame(trades, columns=["Date", "Action", "Price", "Shares"])
        trade_log_df.to_csv("reports/trade_log.csv", index=False)
        print("✅ Trade log saved to reports/trade_log.csv")

        # Performance summary
        returns = df["Total Value"].pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        max_dd = (df["Total Value"] / df["Total Value"].cummax() - 1).min()
        total_trades = len(trade_log_df)

        summary = {
            "Initial Capital": initial_cash,
            "Final Portfolio Value": round(df["Total Value"].iloc[-1], 2),
            "Total Return (%)": round((df["Total Value"].iloc[-1] / initial_cash - 1) * 100, 2),
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown": round(max_dd * 100, 2),
            "Total Trades": total_trades
        }

        summary_df = pd.DataFrame([summary])
        summary_df.to_csv("reports/strategy_summary.csv", index=False)
        print("📤 Summary saved to reports/strategy_summary.csv")

    return df
