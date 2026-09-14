"""Relative-strength-index entry and exit orders."""

import numpy as np
import pandas as pd


def rsi_strategy(
    df: pd.DataFrame,
    rsi_window: int = 14,
    rsi_buy: float = 30,
    rsi_exit: float = 50,
) -> pd.DataFrame:
    """Create long-only RSI entry/exit orders with a persistent holding state."""
    if "Close" not in df:
        raise ValueError("Price data must contain a Close column")
    if not isinstance(rsi_window, int) or rsi_window < 2:
        raise ValueError("rsi_window must be an integer of at least 2")
    if not 0 <= rsi_buy < rsi_exit <= 100:
        raise ValueError("Require 0 <= rsi_buy < rsi_exit <= 100")

    frame = df.copy()
    close = pd.to_numeric(frame["Close"], errors="coerce")
    if close.isna().any() or not np.isfinite(close).all() or (close <= 0).any():
        raise ValueError("Close prices must be finite and positive")

    delta = close.diff()
    average_gain = delta.clip(lower=0).rolling(rsi_window).mean()
    average_loss = (-delta.clip(upper=0)).rolling(rsi_window).mean()
    relative_strength = average_gain / average_loss
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100.0)
    rsi = rsi.mask((average_loss == 0) & (average_gain == 0), 50.0)
    frame["RSI"] = rsi

    regime: list[int] = []
    holding = False
    for value in frame["RSI"]:
        if pd.notna(value):
            if not holding and value < rsi_buy:
                holding = True
            elif holding and value > rsi_exit:
                holding = False
        regime.append(int(holding))

    frame["Signal"] = regime
    frame["Position"] = frame["Signal"].diff().fillna(0.0).astype(float)
    return frame
