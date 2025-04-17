import pandas as pd

def rsi_strategy(df: pd.DataFrame, rsi_window: int = 14, rsi_buy: float = 30, rsi_exit: float = 50) -> pd.DataFrame:
    """
    A more responsive RSI-based trading strategy.
    Buy when RSI < rsi_buy (default 30), exit when RSI > rsi_exit (default 50).
    """
    df = df.copy()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_window).mean()
    loss = -delta.where(delta < 0, 0).rolling(rsi_window).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["Signal"] = 0
    df["Signal"] = df["Signal"].astype(int)

    # Trade logic: Buy below 30, hold until RSI > 50
    holding = False
    for i in range(len(df)):
        if not holding and df["RSI"].iloc[i] < rsi_buy:
            df.at[df.index[i], "Signal"] = 1
            holding = True
        elif holding and df["RSI"].iloc[i] > rsi_exit:
            df.at[df.index[i], "Signal"] = 0
            holding = False
        else:
            df.at[df.index[i], "Signal"] = int(holding)

    df["Position"] = df["Signal"].diff().fillna(0)
    return df
