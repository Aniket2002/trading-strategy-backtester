# Walk-Forward Equity Strategy Backtester

A transparent, single-asset backtesting framework for inspecting signal timing,
portfolio accounting, and transaction-cost sensitivity.

The project implements two deliberately simple technical strategies and an
interactive Streamlit dashboard. Its value is the auditable simulation path—not a
claim that either rule predicts returns. Orders formed from bar *t* are executed on
bar *t+1*, and reported wealth reflects the selected trading-cost assumption.

## Highlights

- SMA/EMA crossover and stateful RSI entry/exit rules.
- Explicit next-bar execution with no position before a signal becomes available.
- Cash and fractional-share accounting for a long-only, all-in position.
- Configurable linear transaction costs applied to traded notional.
- Frictionless buy-and-hold comparison, trade log, Sharpe ratio, and drawdown.
- Deterministic tests for timing, costs, strategy outputs, and invalid inputs.

## Backtest workflow

```text
adjusted daily closes
  -> causal indicator history
  -> entry / exit order on date t
  -> fill at date t+1 close
  -> cash and holdings update
  -> costs, wealth, diagnostics, and buy-and-hold comparison
```

The dashboard downloads the ticker selected by the user through `yfinance`.
The simulation engine itself accepts any `pandas.DataFrame` with positive
`Close` prices and discrete `Position` orders.

## Quick start

```bash
git clone https://github.com/Aniket2002/trading-strategy-backtester.git
cd trading-strategy-backtester
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

The dashboard lets you choose the ticker, sample period, strategy parameters,
initial cash, and transaction cost in basis points.

## Programmatic example

```python
import pandas as pd

from backtest_engine.simulate_strategy import simulate_trading
from strategies.sma_ema import sma_ema_strategy

prices = pd.DataFrame(
    {"Close": [100.0, 101.0, 103.0, 102.0, 104.0, 106.0]}
)
orders = sma_ema_strategy(prices, sma_window=3, ema_window=2)
result = simulate_trading(orders, transaction_cost_bps=10)

print(result[["Close", "Position", "Buy/Sell", "Transaction Cost", "Total Value"]])
```

`Position` means an order event: `1` enters, `-1` exits, and `0` does
nothing. `Buy/Sell` records the later execution event.

## Strategy definitions

### SMA/EMA crossover

The strategy is invested while the exponential moving average is above the simple
moving average. A regime change produces an entry or exit order. The SMA requires a
full window before the first order can be generated.

### RSI regime

RSI uses rolling average gains and losses. The strategy enters below the selected
buy threshold and remains invested until RSI rises above the exit threshold. Flat
windows are assigned an RSI of 50; all-gain windows are assigned 100.

These parameters are user-selected on the full displayed sample. There is no
train/validation/test optimization layer and no parameter-selection claim.

## Execution and metric conventions

- A signal observed at close *t* is filled at close *t+1*.
- Entries invest all available cash; exits sell the full fractional-share holding.
- Transaction cost is `traded_notional * bps / 10,000` on both entry and exit.
- Cash earns no interest; shorting and leverage are not supported.
- Sharpe ratio uses daily portfolio returns, 252-day annualization, and zero
  risk-free rate.
- Drawdown is measured from the running maximum of simulated wealth.
- Buy and hold is a frictionless comparison initialized at the first displayed
  close.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

## Repository structure

```text
backtest_engine/simulate_strategy.py  execution and portfolio accounting
strategies/sma_ema.py                moving-average orders
strategies/rsi.py                    RSI regime orders
tests/test_backtester.py             deterministic timing and cost checks
streamlit_app.py                     data download and interactive presentation
```

## Limitations

- The universe is one currently selected surviving ticker; survivorship bias is not
  controlled.
- Yahoo Finance data can be revised and is not a point-in-time research database.
- Fills use adjusted daily closes and therefore idealize information-processing and
  execution latency.
- Costs are linear; bid/ask spread, slippage, market impact, liquidity, taxes, and
  partial fills are omitted.
- Dividends are represented only through the provider's adjusted-price history.
- Strategy parameters are not estimated on a training set or evaluated on an
  independent holdout.
- The buy-and-hold comparator has no trading costs.

This repository is an educational backtesting-mechanics project, not evidence of
tradable performance and not investment advice.

## License

[MIT](LICENSE)
