"""Interactive presentation layer for the single-asset backtester."""

from datetime import date, timedelta
from io import StringIO

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import streamlit as st
import yfinance as yf

from backtest_engine.simulate_strategy import simulate_trading
from strategies.rsi import rsi_strategy
from strategies.sma_ema import sma_ema_strategy

st.set_page_config(page_title="Equity Strategy Backtester", layout="wide")
st.title("Walk-Forward Equity Strategy Backtester")
st.write(
    "Inspect simple technical rules under explicit next-bar execution and "
    "transaction-cost assumptions. This is an educational single-asset simulator."
)

st.sidebar.header("Backtest assumptions")
strategy_choice = st.sidebar.selectbox(
    "Strategy",
    ["SMA/EMA crossover", "RSI regime"],
)
ticker = st.sidebar.text_input("Ticker", value="AAPL").strip().upper()
today = date.today()
start_date = st.sidebar.date_input("Start date", value=today - timedelta(days=365 * 3))
end_date = st.sidebar.date_input("End date", value=today)
initial_cash = st.sidebar.number_input(
    "Initial cash",
    min_value=1_000.0,
    value=100_000.0,
    step=1_000.0,
)
transaction_cost_bps = st.sidebar.number_input(
    "Transaction cost (bps per traded notional)",
    min_value=0.0,
    value=10.0,
    step=1.0,
)

if strategy_choice == "SMA/EMA crossover":
    sma_window = st.sidebar.slider("SMA window", 10, 200, value=50)
    ema_window = st.sidebar.slider("EMA window", 5, 100, value=20)
    st.sidebar.caption("Enter when the EMA crosses above the SMA; exit when it crosses below.")
else:
    rsi_window = st.sidebar.slider("RSI window", 5, 30, value=14)
    rsi_buy = st.sidebar.slider("RSI entry threshold", 10, 50, value=30)
    minimum_exit = max(40, rsi_buy + 1)
    rsi_exit = st.sidebar.slider(
        "RSI exit threshold",
        minimum_exit,
        80,
        value=max(50, minimum_exit),
    )
    st.sidebar.caption(
        "Enter below the lower threshold and remain invested until RSI exceeds the exit threshold."
    )

run = st.sidebar.button("Run backtest", type="primary")

if not run:
    st.info("Set the assumptions in the sidebar and select **Run backtest**.")
    st.stop()

if not ticker:
    st.error("Enter a ticker.")
    st.stop()
if start_date >= end_date:
    st.error("The start date must be earlier than the end date.")
    st.stop()

try:
    prices = yf.download(
        ticker,
        start=start_date,
        end=end_date + timedelta(days=1),
        auto_adjust=True,
        progress=False,
    )
    if prices.empty:
        st.error("No adjusted price data were returned for this ticker and period.")
        st.stop()

    if isinstance(prices.columns, pd.MultiIndex):
        prices.columns = [column[0] for column in prices.columns]
    else:
        prices.columns = [str(column).strip() for column in prices.columns]

    if strategy_choice == "SMA/EMA crossover":
        frame = sma_ema_strategy(
            prices,
            sma_window=sma_window,
            ema_window=ema_window,
        )
    else:
        frame = rsi_strategy(
            prices,
            rsi_window=rsi_window,
            rsi_buy=rsi_buy,
            rsi_exit=rsi_exit,
        )

    frame = simulate_trading(
        frame,
        initial_cash=float(initial_cash),
        transaction_cost_bps=float(transaction_cost_bps),
    )
except (ValueError, RuntimeError) as exc:
    st.error(f"Backtest could not run: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"Data download or application error: {exc}")
    st.stop()

st.subheader(f"{strategy_choice}: {ticker}")
st.caption(
    f"{frame.index.min().date()} to {frame.index.max().date()} · adjusted daily "
    "closes · orders filled at the next close · fractional shares · no shorting"
)

price_figure = go.Figure()
price_figure.add_trace(
    go.Scatter(x=frame.index, y=frame["Close"], mode="lines", name="Adjusted close")
)
if "SMA" in frame:
    price_figure.add_trace(go.Scatter(x=frame.index, y=frame["SMA"], mode="lines", name="SMA"))
if "EMA" in frame:
    price_figure.add_trace(go.Scatter(x=frame.index, y=frame["EMA"], mode="lines", name="EMA"))

buy_fills = frame[frame["Buy/Sell"] == "BUY"]
sell_fills = frame[frame["Buy/Sell"] == "SELL"]
price_figure.add_trace(
    go.Scatter(
        x=buy_fills.index,
        y=buy_fills["Close"],
        mode="markers",
        marker={"symbol": "triangle-up", "size": 10},
        name="Buy fill",
    )
)
price_figure.add_trace(
    go.Scatter(
        x=sell_fills.index,
        y=sell_fills["Close"],
        mode="markers",
        marker={"symbol": "triangle-down", "size": 10},
        name="Sell fill",
    )
)
price_figure.update_layout(height=480, margin={"l": 20, "r": 20, "t": 30, "b": 20})
st.plotly_chart(price_figure, use_container_width=True)

if "RSI" in frame:
    st.subheader("RSI")
    st.line_chart(frame["RSI"], use_container_width=True)

buy_and_hold = float(initial_cash) * frame["Close"] / frame["Close"].iloc[0]
wealth = pd.DataFrame(
    {
        "Strategy": frame["Total Value"],
        "Buy and hold (frictionless)": buy_and_hold,
    }
)
st.subheader("Portfolio comparison")
st.line_chart(wealth, use_container_width=True)

returns = frame["Total Value"].pct_change().dropna()
volatility = returns.std(ddof=1)
sharpe = (
    float(returns.mean() / volatility * np.sqrt(252))
    if len(returns) > 1 and np.isfinite(volatility) and volatility > 0
    else 0.0
)
strategy_return = frame["Total Value"].iloc[-1] / float(initial_cash) - 1
benchmark_return = buy_and_hold.iloc[-1] / float(initial_cash) - 1
drawdown = (frame["Total Value"] / frame["Total Value"].cummax() - 1).min()
trades = int(frame["Buy/Sell"].isin(["BUY", "SELL"]).sum())

columns = st.columns(6)
columns[0].metric("Final value", f"${frame['Total Value'].iloc[-1]:,.2f}")
columns[1].metric("Strategy return", f"{strategy_return:.2%}")
columns[2].metric("Buy-and-hold return", f"{benchmark_return:.2%}")
columns[3].metric("Sharpe (rf=0)", f"{sharpe:.2f}")
columns[4].metric("Max drawdown", f"{drawdown:.2%}")
columns[5].metric("Trades", f"{trades}")
st.caption(f"Cumulative modelled transaction cost: ${frame['Transaction Cost'].sum():,.2f}")

st.subheader("Executed trades")
trade_log = frame.loc[
    frame["Buy/Sell"].isin(["BUY", "SELL"]),
    ["Buy/Sell", "Close", "Transaction Cost"],
].copy()
trade_log["Date"] = trade_log.index
trade_log = trade_log.rename(columns={"Buy/Sell": "Action", "Close": "Price"})[
    ["Date", "Action", "Price", "Transaction Cost"]
]
st.dataframe(trade_log, hide_index=True, use_container_width=True)

csv_buffer = StringIO()
trade_log.to_csv(csv_buffer, index=False)
st.download_button(
    "Download trade log",
    csv_buffer.getvalue(),
    file_name="trade_log.csv",
    mime="text/csv",
)

st.warning(
    "Limitations: Yahoo Finance data may be revised; the universe is one "
    "surviving ticker selected today; fills use the next daily close with "
    "fractional shares; costs are linear; dividends, slippage, spreads, taxes, "
    "liquidity, and parameter holdouts are not modelled."
)
