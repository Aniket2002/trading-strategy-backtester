# 📈 TradePilot – A Backtesting Engine for Trading Strategies

**TradePilot** is a modular backtesting framework for evaluating rule-based and ML-powered trading strategies on historical market data. Designed with a focus on clean architecture, reproducibility, and extensibility, it simulates how trading strategies would perform in real-world conditions.

---

## 🚀 Features

- 📊 Load historical stock data using `yfinance`
- ⚙️ Plug-and-play strategy architecture (SMA/EMA crossover, ML models, etc.)
- 🧪 Backtest engine with portfolio simulation
- 📉 Metrics: cumulative returns, drawdowns, Sharpe ratio, and more
- 📁 Modular structure for easy experimentation and scaling

---

## 📂 Project Structure

backtesting-ml-strategies/

├── data/               # Raw and cleaned historical data
├── notebooks/          # EDA and strategy research notebooks
├── strategies/         # Strategy definitions (rule-based and ML)
├── backtest_engine/    # Core simulation logic and trade tracking
├── reports/            # Performance visualizations and logs
├── requirements.txt    # Project dependencies
└── README.md           # Project overview

---

## 🧠 Strategy Example (WIP)

> **SMA/EMA Crossover:** Buy when short-term average crosses above long-term average, sell when it crosses below. Simple but a good starting benchmark.

---

## 📈 Next Steps

- [ ] Add basic SMA/EMA crossover logic
- [ ] Implement a backtest simulator
- [ ] Visualize performance (returns, drawdowns)
- [ ] Explore ML-based strategies

---

## 📦 Dependencies

To be installed from `requirements.txt`. Primary libraries:
- `yfinance`
- `pandas`
- `numpy`
- `matplotlib` / `plotly`
- `sklearn` (for ML strategies)

---

## 🧰 Ideal For

- Tech professionals entering quant finance
- Algo trading enthusiasts
- Anyone wanting to simulate and validate trading ideas

---
