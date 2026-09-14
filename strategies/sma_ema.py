"""Moving-average crossover orders."""

import numpy as np
import pandas as pd


def sma_ema_strategy(
    df: pd.DataFrame,
    sma_window: int = 50,
    ema_window: int = 20,
) -> pd.DataFrame:
    """Create long-only entry/exit orders from an EMA/SMA regime."""
    if "Close" not in df:
        raise ValueError("Price data must contain a Close column")
    if (
        not isinstance(sma_window, int)
        or not isinstance(ema_window, int)
        or sma_window < 2
        or ema_window < 2
    ):
        raise ValueError("Moving-average windows must be integers of at least 2")

    frame = df.copy()
    close = pd.to_numeric(frame["Close"], errors="coerce")
    if close.isna().any() or not np.isfinite(close).all() or (close <= 0).any():
        raise ValueError("Close prices must be finite and positive")

    frame["SMA"] = close.rolling(window=sma_window).mean()
    frame["EMA"] = close.ewm(span=ema_window, adjust=False).mean()
    frame["Signal"] = (frame["EMA"] > frame["SMA"]).astype(int)
    frame["Position"] = frame["Signal"].diff().fillna(0.0).astype(float)
    return frame
