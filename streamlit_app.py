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

st.markdown("""
Welcome to **Strategy-Gamble** 🎰 — a beginner-friendly trading strategy simulator.

Here's what you're about to do:

1. Choose a stock and time range 📅  
2. Define how sensitive the signals should be via SMA/EMA sliders 🎚️  
3. Run a backtest that simulates buying/selling based on those signals 💰  
4. See how your strategy would have performed 📈

No experience needed — scroll through each section and let the app guide you.
""")

# Sidebar input
st.sidebar.header("⚙️ Parameters")
ticker = st.sidebar.text_input("Ticker", placeholder="e.g. AAPL").upper()
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")
sma_win = st.sidebar.slider(
    "SMA Window", 10, 200,
    help="Simple Moving Average: mean of the last N closing prices."
)
ema_win = st.sidebar.slider(
    "EMA Window", 5, 100,
    help="Exponential Moving Average: recent prices have more weight."
)

if st.sidebar.button("🚀 Run Strategy"):
    st.subheader(f"Backtest for {ticker} from {start_date} to {end_date}")

    try:
        # Fetch data
        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            st.error("⚠️ No data found for this ticker/date range.")
            st.stop()

        # Flatten weird columns if needed
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

        # Simulate backtest
        df = simulate_trading(df, save_reports=False)

        # 📊 Price chart explanation
        st.markdown("""
### 📊 Price + Signals

This chart shows how your chosen stock moved over time, along with two indicators:

- **SMA (Simple Moving Average)** — smooths out past prices evenly  
- **EMA (Exponential Moving Average)** — gives more weight to recent prices  

**Green ↑ = Buy signal** when EMA crosses above SMA  
**Red ↓ = Sell signal** when EMA crosses below SMA
""")
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
        st.markdown("""
### 💼 Portfolio Value Over Time

This simulates what would’ve happened if you started with $100,000 and only bought/sold when the signals told you to.

- The line goes **up** when your strategy worked well  
- It flattens when you're **not in a trade**
""")
        st.line_chart(df["Total Value"], use_container_width=True)

        # 📈 Strategy metrics
        st.markdown("""
### 📈 Strategy Metrics

These numbers summarize how your trading decisions played out:

- **Final Value** — how much you’d have if you followed this strategy  
- **Return (%)** — percentage gain or loss from your $100,000  
- **Sharpe Ratio** — how good the returns were *relative to risk* (above 1 is solid)  
- **Max Drawdown** — worst drop from peak value (lower = safer)  
- **Total Trades** — how often you bought/sold
""")
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
        st.markdown("""
### 📋 Trade Log

Here’s every buy and sell your strategy made — with the date and price:

- **BUY**: You entered the trade  
- **SELL**: You exited (hopefully at a profit!)
""")
        trade_log = df[df["Buy/Sell"].isin(["BUY", "SELL"])][["Buy/Sell", "Close"]].copy()
        trade_log["Date"] = trade_log.index
        trade_log.rename(columns={"Buy/Sell": "Action", "Close": "Price"}, inplace=True)
        st.dataframe(trade_log.reset_index(drop=True))

        # 📥 Trade log download
        st.markdown("⬇️ Download your trade history to keep track or share with others:")
        csv_buffer = StringIO()
        trade_log.to_csv(csv_buffer, index=False)
        st.download_button("📥 Download Trade Log CSV", csv_buffer.getvalue(), file_name="trade_log.csv", mime="text/csv")

    except Exception as e:
        st.error(f"🚨 Strategy failed to run: {e}")
        st.stop()
