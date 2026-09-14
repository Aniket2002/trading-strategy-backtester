import numpy as np
import pandas as pd
import pytest

from backtest_engine.simulate_strategy import simulate_trading
from strategies.rsi import rsi_strategy
from strategies.sma_ema import sma_ema_strategy


def order_frame() -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=4, freq="D")
    return pd.DataFrame(
        {
            "Close": [100.0, 100.0, 110.0, 110.0],
            "Position": [1.0, 0.0, -1.0, 0.0],
        },
        index=index,
    )


def test_orders_execute_on_next_bar() -> None:
    result = simulate_trading(order_frame())

    assert result["Buy/Sell"].tolist() == ["", "BUY", "", "SELL"]
    assert result.iloc[0]["Holdings"] == pytest.approx(0.0)
    assert result.iloc[1]["Holdings"] == pytest.approx(100_000)
    assert result.iloc[-1]["Total Value"] == pytest.approx(110_000)


def test_transaction_costs_reduce_wealth() -> None:
    frictionless = simulate_trading(order_frame(), transaction_cost_bps=0)
    with_costs = simulate_trading(order_frame(), transaction_cost_bps=10)

    assert with_costs["Transaction Cost"].sum() > 0
    assert with_costs.iloc[-1]["Total Value"] < frictionless.iloc[-1]["Total Value"]


def test_report_export_is_explicit(tmp_path) -> None:
    simulate_trading(order_frame(), save_reports=False, reports_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []

    simulate_trading(order_frame(), save_reports=True, reports_dir=tmp_path)
    assert {path.name for path in tmp_path.iterdir()} == {
        "strategy_summary.csv",
        "trade_log.csv",
    }


@pytest.mark.parametrize(
    ("column", "values"),
    [
        ("Close", [100.0, 0.0, 101.0, 102.0]),
        ("Position", [0.0, 0.5, 0.0, 0.0]),
    ],
)
def test_simulator_rejects_invalid_financial_inputs(column, values) -> None:
    frame = order_frame()
    frame[column] = values
    with pytest.raises(ValueError):
        simulate_trading(frame)


def test_sma_ema_strategy_emits_only_discrete_orders() -> None:
    frame = pd.DataFrame({"Close": np.linspace(80.0, 120.0, 30)})
    result = sma_ema_strategy(frame, sma_window=10, ema_window=3)

    assert set(result["Position"].unique()).issubset({-1.0, 0.0, 1.0})
    assert result["SMA"].iloc[:9].isna().all()


def test_rsi_handles_flat_and_one_directional_windows() -> None:
    frame = pd.DataFrame({"Close": [100.0] * 5 + [101.0, 102.0, 103.0, 104.0, 105.0]})
    result = rsi_strategy(frame, rsi_window=3)

    assert result["RSI"].iloc[3] == pytest.approx(50.0)
    assert result["RSI"].iloc[-1] == pytest.approx(100.0)
    assert set(result["Position"].unique()).issubset({-1.0, 0.0, 1.0})
