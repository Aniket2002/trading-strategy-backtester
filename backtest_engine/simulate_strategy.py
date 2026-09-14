"""Single-asset, long-only portfolio simulation."""

from pathlib import Path

import numpy as np
import pandas as pd


def _validate_inputs(
    frame: pd.DataFrame,
    initial_cash: float,
    transaction_cost_bps: float,
) -> None:
    required = {"Close", "Position"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Price data cannot be empty")
    if not np.isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("initial_cash must be finite and positive")
    if not np.isfinite(transaction_cost_bps) or transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps must be finite and nonnegative")

    close = pd.to_numeric(frame["Close"], errors="coerce")
    orders = pd.to_numeric(frame["Position"], errors="coerce")
    if close.isna().any() or not np.isfinite(close).all() or (close <= 0).any():
        raise ValueError("Close prices must be finite and positive")
    if orders.isna().any() or not np.isfinite(orders).all():
        raise ValueError("Position values must be finite")
    if not orders.isin([-1.0, 0.0, 1.0]).all():
        raise ValueError("Position must contain only entry (1), exit (-1), or hold (0)")


def simulate_trading(
    df: pd.DataFrame,
    initial_cash: float = 100_000.0,
    transaction_cost_bps: float = 0.0,
    save_reports: bool = False,
    reports_dir: str | Path = "reports",
) -> pd.DataFrame:
    """Simulate next-bar execution of long-only entry and exit orders.

    A `Position` value generated on bar *t* is filled at the closing price on
    bar *t+1*. Entry orders invest all available cash and exit orders liquidate
    the full fractional-share position. Linear transaction costs apply to traded
    notional. The default cost is zero for backward-compatible comparisons.
    """
    frame = df.copy()
    _validate_inputs(frame, initial_cash, transaction_cost_bps)

    cash = float(initial_cash)
    holdings = 0.0
    cost_rate = float(transaction_cost_bps) / 10_000.0
    portfolio_values: list[tuple[float, float, float, str, float]] = []
    trades: list[tuple[object, str, float, float, float]] = []

    execution_orders = frame["Position"].shift(1).fillna(0.0)

    for idx, price, order in zip(
        frame.index,
        frame["Close"].astype(float),
        execution_orders,
        strict=True,
    ):
        action = ""
        shares_traded = 0.0
        transaction_cost = 0.0

        if order == 1.0 and cash > 0:
            shares_traded = cash / (price * (1.0 + cost_rate))
            traded_notional = shares_traded * price
            transaction_cost = traded_notional * cost_rate
            holdings = shares_traded
            cash -= traded_notional + transaction_cost
            action = "BUY"
        elif order == -1.0 and holdings > 0:
            shares_traded = holdings
            traded_notional = shares_traded * price
            transaction_cost = traded_notional * cost_rate
            cash += traded_notional - transaction_cost
            holdings = 0.0
            action = "SELL"

        if abs(cash) < 1e-10:
            cash = 0.0
        holdings_value = holdings * price
        total_value = cash + holdings_value
        portfolio_values.append((cash, holdings_value, total_value, action, transaction_cost))
        if action:
            trades.append((idx, action, price, shares_traded, transaction_cost))

    (
        frame["Cash"],
        frame["Holdings"],
        frame["Total Value"],
        frame["Buy/Sell"],
        frame["Transaction Cost"],
    ) = zip(*portfolio_values, strict=True)

    if save_reports:
        destination = Path(reports_dir)
        destination.mkdir(parents=True, exist_ok=True)
        trade_log = pd.DataFrame(
            trades,
            columns=["Date", "Action", "Price", "Shares", "Transaction Cost"],
        )
        trade_log.to_csv(destination / "trade_log.csv", index=False)

        returns = frame["Total Value"].pct_change().dropna()
        volatility = returns.std(ddof=1)
        sharpe = (
            float(returns.mean() / volatility * np.sqrt(252))
            if len(returns) > 1 and np.isfinite(volatility) and volatility > 0
            else 0.0
        )
        max_drawdown = (frame["Total Value"] / frame["Total Value"].cummax() - 1).min()
        summary = {
            "Initial Capital": initial_cash,
            "Final Portfolio Value": round(frame["Total Value"].iloc[-1], 2),
            "Total Return (%)": round(
                (frame["Total Value"].iloc[-1] / initial_cash - 1) * 100,
                2,
            ),
            "Sharpe Ratio (rf=0)": round(sharpe, 2),
            "Max Drawdown (%)": round(max_drawdown * 100, 2),
            "Total Trades": len(trade_log),
            "Transaction Cost (bps)": transaction_cost_bps,
            "Cumulative Transaction Cost": round(
                frame["Transaction Cost"].sum(),
                2,
            ),
        }
        pd.DataFrame([summary]).to_csv(
            destination / "strategy_summary.csv",
            index=False,
        )

    return frame
