import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import importlib
from io import StringIO

from strategies.sma_ema import sma_ema_strategy
from strategies.rsi import rsi_strategy
import backtest_engine.simulate_strategy as sim
importlib.reload(sim)
from backtest_engine.simulate_strategy import simulate_trading

# 📐 Compact layout: reduce top/bottom padding
st.set_page_config(page_title="Strategy Backtester", layout="wide")
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    section.main > div:first-child {
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] {
        padding-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title and intro
st.markdown("<h1 style='color:#00C49F'>🎰 Strategy-Gamble Backtester</h1>", unsafe_allow_html=True)

st.markdown("""
Welcome to **Strategy-Gamble** — an interactive tool to visualize how trading strategies would have performed on real stock data.

This app lets you:
- Backtest SMA/EMA and RSI strategies  
- Simulate trades and view performance  
- Download trade logs  
- Understand key metrics — beginner-friendly
""")

# Sidebar controls
st.sidebar.header("⚙️ Parameters")
strategy_choice = st.sidebar.selectbox("Select Strategy", ["SMA/EMA Crossover", "RSI Strategy"])

with st.sidebar.expander("📘 Strategy Description"):
    if strategy_choice == "SMA/EMA Crossover":
        st.markdown("""
**SMA/EMA Crossover**

Buy when **EMA crosses above SMA**  
Sell when **EMA crosses below SMA**
        """)
    else:
        st.markdown("""
**RSI Strategy**

Buy when **RSI < 30** (oversold)  
Sell when **RSI > 50** (momentum reversal)
        """)

ticker = st.sidebar.text_input("Ticker", placeholder="e.g. AAPL").upper()
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

if strategy_choice == "SMA/EMA Crossover":
    sma_win = st.sidebar.slider("SMA Window", 10, 200, value=50)
    ema_win = st.sidebar.slider("EMA Window", 5, 100, value=20)

if strategy_choice == "RSI Strategy":
    rsi_window = st.sidebar.slider("RSI Window", 5, 30, value=14)
    rsi_buy = st.sidebar.slider("RSI Buy Threshold", 10, 50, value=30)
    rsi_sell = st.sidebar.slider("RSI Exit Threshold", 40, 70, value=50)

# 🚀 Button (now visible immediately)
if st.sidebar.button("🚀 Run Strategy"):
    st.subheader(f"{strategy_choice} on {ticker} from {start_date} to {end_date}")

    try:
        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            st.error("⚠️ No data found for this ticker/date range.")
            st.stop()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        else:
            df.columns = [str(col).strip() for col in df.columns]

        df.drop(columns=["Adj Close"], inplace=True, errors="ignore")
        df.reset_index(inplace=True)
        df.set_index("Date", inplace=True)

        if strategy_choice == "SMA/EMA Crossover":
            df = sma_ema_strategy(df, sma_window=sma_win, ema_window=ema_win)
        else:
            df = rsi_strategy(df, rsi_window=rsi_window, rsi_buy=rsi_buy, rsi_exit=rsi_sell)

        if "Position" not in df.columns:
            st.error("❌ Strategy output missing 'Position' column.")
            st.write("🧪 Debug - Columns in DataFrame:", df.columns.tolist())
            st.stop()

        df = simulate_trading(df, save_reports=False)

        st.markdown("<h3 style='color:#00C49F'>📊 Interactive Price Chart + Signals</h3>", unsafe_allow_html=True)

        price_fig = go.Figure()
        price_fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode='lines', name='Close', line=dict(color='white')))
        if "SMA" in df.columns:
            price_fig.add_trace(go.Scatter(x=df.index, y=df["SMA"], mode='lines', name='SMA', line=dict(dash='dash', color='cyan')))
        if "EMA" in df.columns:
            price_fig.add_trace(go.Scatter(x=df.index, y=df["EMA"], mode='lines', name='EMA', line=dict(dash='dot', color='orange')))

        buy_signals = df[df["Position"] == 1]
        sell_signals = df[df["Position"] == -1]

        price_fig.add_trace(go.Scatter(
            x=buy_signals.index, y=buy_signals["Close"],
            mode='markers', marker=dict(symbol='triangle-up', size=10, color='lime'),
            name='BUY Signal'
        ))
        price_fig.add_trace(go.Scatter(
            x=sell_signals.index, y=sell_signals["Close"],
            mode='markers', marker=dict(symbol='triangle-down', size=10, color='red'),
            name='SELL Signal'
        ))

        price_fig.update_layout(
            height=500,
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
            font=dict(color='white'),
            legend=dict(bgcolor='rgba(0,0,0,0)', borderwidth=0),
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(price_fig, use_container_width=True)

        if "RSI" in df.columns:
            st.markdown("<h3 style='color:#00C49F'>📉 RSI Indicator</h3>", unsafe_allow_html=True)
            with st.expander("📖 What does this show?"):
                st.markdown("Relative Strength Index (RSI) tracks momentum. <30 = oversold (buy), >70 = overbought (sell).")
            st.line_chart(df["RSI"], use_container_width=True)

        st.markdown("<h3 style='color:#00C49F'>💼 Portfolio Value Over Time</h3>", unsafe_allow_html=True)
        st.line_chart(df["Total Value"], use_container_width=True)

        st.markdown("<h3 style='color:#00C49F'>📈 Strategy Metrics</h3>", unsafe_allow_html=True)
        final_val = df["Total Value"].iloc[-1]
        ret_pct = round((final_val / 100000 - 1) * 100, 2)
        sharpe = df["Total Value"].pct_change().mean() / df["Total Value"].pct_change().std() * (252 ** 0.5)
        drawdown = (df["Total Value"] / df["Total Value"].cummax() - 1).min() * 100
        trades = df["Buy/Sell"].isin(["BUY", "SELL"]).sum()

        cols = st.columns(4)
        cols[0].metric("Final Value", f"${final_val:,.2f}")
        cols[1].metric("Return (%)", f"{ret_pct:.2f}%")
        cols[2].metric("Sharpe", f"{sharpe:.2f}")
        cols[3].metric("Max Drawdown", f"{drawdown:.2f}%")
        st.caption(f"🔁 Total Trades: {trades}")

        st.markdown("<h3 style='color:#00C49F'>📋 Trade Log</h3>", unsafe_allow_html=True)
        trade_log = df[df["Buy/Sell"].isin(["BUY", "SELL"])][["Buy/Sell", "Close"]].copy()
        trade_log["Date"] = trade_log.index
        trade_log.rename(columns={"Buy/Sell": "Action", "Close": "Price"}, inplace=True)
        st.dataframe(trade_log.reset_index(drop=True))

        csv_buffer = StringIO()
        trade_log.to_csv(csv_buffer, index=False)
        st.download_button("📥 Download Trade Log CSV", csv_buffer.getvalue(), file_name="trade_log.csv", mime="text/csv")

    except Exception as e:
        st.error(f"🚨 Strategy failed to run: {e}")
        st.stop()
