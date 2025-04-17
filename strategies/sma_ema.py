import pandas as pd

def sma_ema_strategy(df: pd.DataFrame, sma_window: int = 50, ema_window: int = 20) -> pd.DataFrame:
    """
    Applies an SMA/EMA crossover strategy to the price DataFrame.

    Args:
        df (pd.DataFrame): Price data with a 'Close' column.
        sma_window (int): Window size for the SMA.
        ema_window (int): Window size for the EMA.

    Returns:
        pd.DataFrame: Original DataFrame with added columns:
                      ['SMA', 'EMA', 'Signal', 'Position']
    """
    df = df.copy()

    # Indicators
    df["SMA"] = df["Close"].rolling(window=sma_window).mean()
    df["EMA"] = df["Close"].ewm(span=ema_window, adjust=False).mean()

    # Signal: 1 if EMA > SMA, else 0
    df["Signal"] = 0
    df.loc[df["EMA"] > df["SMA"], "Signal"] = 1

    # Position: diff of signal (1 = buy, -1 = sell, 0 = hold)
    df["Position"] = df["Signal"].diff().fillna(0).astype(float)


    return df
