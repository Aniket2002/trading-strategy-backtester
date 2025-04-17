import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import importlib
from io import StringIO

from strategies.sma_ema import sma_ema_strategy
import backtest_engine.simulate_strategy as sim
importlib.reload(sim)
from backtest_engine.simulate_strategy import simulate_trading

st.set_page_config(page_title="Strategy Backtester", layout="wide")
st.title("📈 SMA/EMA Strategy Backtester")

st.sidebar.header("⚙️ Parameters")
ticker = st.sidebar.text_input("Ticker", value="AAPL").upper()
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2018-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-12-31"))
sma_win = st.sidebar.slider(
    "SMA Window", 10, 200, 50,
    help="Simple Moving Average: mean of the last N closing prices."
)
ema_win = st.sidebar.slider(
    "EMA Window", 5, 100, 20,
    help="Exponential Moving Average: recent prices have more weight."
)

if st.sidebar.button("🚀 Run Strategy"):
    st.subheader(f"Backtest for {ticker} from {start_date} to {end_date}")

    try:
        df = yf.download(ticker, start=start_date, end=end_date)

        if df.empty:
            st.error("⚠️ No data found for this ticker/date range.")
            st.stop()

        # Flatten multi-index if necessary
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        else:
            df.columns = [str(col).strip() for col in df.columns]

        df.drop(columns=["Adj Close"], inplace=True, errors="ignore")
        df.reset_index(inplace=True)
        df.set_index("Date", inplace=True)

        # Apply strategy
        df = sma_ema_strategy(df, sma_window=sma_win, ema_window=ema_win)

        if "Position" not in df.columns:
            st.error("❌ Strategy output missing 'Position' column.")
            st.write("🧪 Debug - Columns in DataFrame:", df.columns.tolist())
            st.stop()

        df = simulate_trading(df, save_reports=False)

        # 📊 Price chart
        st.markdown("### 📊 Price + Signals")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df["Close"], label="Close", alpha=0.6)
        ax.plot(df["SMA"], label=f"SMA {sma_win}", linestyle="--")
        ax.plot(df["EMA"], label=f"EMA {ema_win}", linestyle=":")
        ax.scatter(df[df["Buy/Sell"] == "BUY"].index, df[df["Buy/Sell"] == "BUY"]["Close"], label="BUY", marker="^", color="green", s=100)
        ax.scatter(df[df["Buy/Sell"] == "SELL"].index, df[df["Buy/Sell"] == "SELL"]["Close"], label="SELL", marker="v", color="red", s=100)
        ax.set_title("Price Chart with Trade Signals")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # 💼 Portfolio chart
        st.markdown("### 💼 Portfolio Value Over Time")
        st.line_chart(df["Total Value"], use_container_width=True)

        # 📈 Metrics
        st.markdown("### 📈 Strategy Metrics")
        final_val = df["Total Value"].iloc[-1]
        ret_pct = round((final_val / 100000 - 1) * 100, 2)
        sharpe = df["Total Value"].pct_change().mean() / df["Total Value"].pct_change().std() * (252 ** 0.5)
        drawdown = (df["Total Value"] / df["Total Value"].cummax() - 1).min() * 100
        trades = df["Buy/Sell"].isin(["BUY", "SELL"]).sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Final Value", f"${final_val:,.2f}")
        col2.metric("Return (%)", f"{ret_pct:.2f}%")
        col3.metric("Sharpe", f"{sharpe:.2f}")
        col4.metric("Max Drawdown", f"{drawdown:.2f}%")

        # 📋 Trade log
        st.markdown("### 📋 Trade Log")
        trade_log = df[df["Buy/Sell"].isin(["BUY", "SELL"])][["Buy/Sell", "Close"]].copy()
        trade_log["Date"] = trade_log.index
        trade_log.rename(columns={"Buy/Sell": "Action", "Close": "Price"}, inplace=True)
        st.dataframe(trade_log.reset_index(drop=True))

        # 📥 Download trade log
        csv_buffer = StringIO()
        trade_log.to_csv(csv_buffer, index=False)
        st.download_button("📥 Download Trade Log CSV", csv_buffer.getvalue(), file_name="trade_log.csv", mime="text/csv")

    except Exception as e:
        st.error(f"🚨 Strategy failed to run: {e}")
        st.stop()
