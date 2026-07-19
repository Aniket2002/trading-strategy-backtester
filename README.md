# Walk-Forward Equity Strategy Backtester

A Streamlit-powered backtesting dashboard for educational walk-forward strategy simulation and diagnostics.

---

## 🚀 Features

- 📈 SMA/EMA crossover trading strategy
- 💰 Portfolio growth tracking
- 🧮 Sharpe ratio, drawdown, and trade metrics
- 🔁 Buy/sell signal markers
- 📋 Trade logs and performance exports
- 🎨 Interactive Streamlit UI with clean dark theme

---

## 📦 Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/Aniket2002/trading-strategy-backtester.git
cd trading-strategy-backtester

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run streamlit_app.py
```

---

## 📊 Strategy Logic

This dashboard uses a simple **SMA/EMA crossover** strategy:

- 📈 **Buy** when the EMA crosses above the SMA  
- 📉 **Sell** when the EMA crosses below the SMA  
- Simulated with $100,000 initial capital  
- Tracks portfolio value, trades, and cumulative performance

All price data is sourced from [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` API.

---

## Notes

This project is intended for educational backtesting. Signals are executed on the next bar in the simulator to reduce look-ahead bias.
