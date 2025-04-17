import pandas as pd

def sma_ema_strategy(
    df: pd.DataFrame,
    sma_window: int = 50,
    ema_window: int = 20
) -> pd.DataFrame:
    """
    Applies SMA/EMA crossover strategy to the given DataFrame.

    Parameters:
        df (pd.DataFrame): DataFrame with at least a 'Close' column.
        sma_window (int): Window size for Simple Moving Average.
        ema_window (int): Window size for Exponential Moving Average.

    Returns:
        pd.DataFrame: Original DataFrame with added strategy columns:
            ['SMA', 'EMA', 'Signal', 'Position']
    """
    df = df.copy()

    # Calculate moving averages
    df["SMA"] = df["Close"].rolling(window=sma_window).mean()
    df["EMA"] = df["Close"].ewm(span=ema_window, adjust=False).mean()

    # Generate signals
    df["Signal"] = 0
    df.loc[df["EMA"] > df["SMA"], "Signal"] = 1
    df.loc[df["EMA"] < df["SMA"], "Signal"] = 0

    # Create position column: 1 = buy, 0 = hold/cash
    df["Position"] = df["Signal"].diff()

    return df
