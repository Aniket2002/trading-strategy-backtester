import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import os
import importlib

# Local strategy + engine
from strategies.sma_ema import sma_ema_strategy
import backtest_engine.simulate_strategy as sim
importlib.reload(sim)
from backtest_engine.simulate_strategy import simulate_trading

st.set_page_config(page_title="Trading Strategy Backtester", layout="wide")

st.title("📈 SMA/EMA Strategy Backtester")
st.markdown("Run technical trading strategies and visualize performance on historical stock data.")

# Sidebar controls
st.sidebar.header("⚙️ Strategy Parameters")

ticker = st.sidebar.text_input("Stock Ticker", value="AAPL").upper()
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2018-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-12-31"))

sma_window = st.sidebar.slider("SMA Window", 10, 200, 50)
ema_window = st.sidebar.slider("EMA Window", 5, 100, 20)

run_button = st.sidebar.button("🚀 Run Strategy")

# Run logic
if run_button:
    st.subheader(f"Backtest for {ticker} from {start_date} to {end_date}")
    
    # Fetch data
    df = yf.download(ticker, start=start_date, end=end_date)
    if df.empty:
        st.error("No data found for this ticker/date range.")
    else:
        df = df.drop(columns=["Adj Close"], errors="ignore")
        df.reset_index(inplace=True)
        df.set_index("Date", inplace=True)

        # Strategy logic
        try:
            # Run strategy logic
            df = sma_ema_strategy(df, sma_window=sma_window, ema_window=ema_window)
            df = simulate_trading(df, save_reports=False)

        except Exception as e:
            st.error(f"🚨 Strategy failed to run: {e}")
            st.stop()


        # Plots
        st.markdown("### 📉 Price Chart with Signals")
        fig, ax = plt.subplots()
        ax.plot(df["Close"], label="Close Price", alpha=0.6)
        ax.plot(df["SMA"], label=f"SMA {sma_window}", linestyle="--")
        ax.plot(df["EMA"], label=f"EMA {ema_window}", linestyle=":")
        ax.scatter(df[df["Buy/Sell"] == "BUY"].index, df[df["Buy/Sell"] == "BUY"]["Close"], label="BUY", color="green", marker="^", s=100)
        ax.scatter(df[df["Buy/Sell"] == "SELL"].index, df[df["Buy/Sell"] == "SELL"]["Close"], label="SELL", color="red", marker="v", s=100)
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # Portfolio performance
        st.markdown("### 💼 Portfolio Value Over Time")
        st.line_chart(df["Total Value"])

        # Metrics
        st.markdown("### 📊 Strategy Summary")
        final_value = df["Total Value"].iloc[-1]
        initial = 100000
        returns = (final_value / initial - 1) * 100
        sharpe = df["Total Value"].pct_change().mean() / df["Total Value"].pct_change().std() * (252**0.5)
        drawdown = (df["Total Value"] / df["Total Value"].cummax() - 1).min() * 100
        trades = df["Buy/Sell"].isin(["BUY", "SELL"]).sum()

        st.metric("💰 Final Portfolio Value", f"${final_value:,.2f}")
        st.metric("📈 Total Return", f"{returns:.2f}%")
        st.metric("⚖️ Sharpe Ratio", f"{sharpe:.2f}")
        st.metric("📉 Max Drawdown", f"{drawdown:.2f}%")
        st.metric("🔁 Total Trades", trades)

        # Trade Log
        st.markdown("### 📋 Trade Log")
        trade_log = df[df["Buy/Sell"].isin(["BUY", "SELL"])][["Buy/Sell", "Close"]].copy()
        trade_log["Date"] = trade_log.index
        trade_log.rename(columns={"Buy/Sell": "Action", "Close": "Price"}, inplace=True)
        st.dataframe(trade_log.reset_index(drop=True))
