import pandas as pd
import numpy as np


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
         ) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast   = close.ewm(span=fast,   adjust=False).mean()
    ema_slow   = close.ewm(span=slow,   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line, macd_line - signal_line


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
        ) -> tuple[pd.Series, pd.Series, pd.Series]:
    plus_dm  = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    # Zero out when the other direction is larger
    mask = plus_dm < minus_dm
    plus_dm[mask] = 0
    mask2 = minus_dm < plus_dm
    minus_dm[mask2] = 0

    tr_val    = atr(high, low, close, 1)
    atr_val   = tr_val.rolling(period).mean()
    plus_di   = 100 * plus_dm.rolling(period).mean()  / atr_val.replace(0, np.nan)
    minus_di  = 100 * minus_dm.rolling(period).mean() / atr_val.replace(0, np.nan)
    dx        = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.rolling(period).mean(), plus_di, minus_di


def bollinger(close: pd.Series, period: int = 20, mult: float = 2.0
              ) -> tuple[pd.Series, pd.Series, pd.Series]:
    ma  = close.rolling(period).mean()
    std = close.rolling(period).std()
    return ma + mult * std, ma, ma - mult * std


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
               k_period: int = 14, d_period: int = 3) -> tuple[pd.Series, pd.Series]:
    ll = low.rolling(k_period).min()
    hh = high.rolling(k_period).max()
    k  = 100 * (close - ll) / (hh - ll).replace(0, np.nan)
    return k, k.rolling(d_period).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    return close.ewm(span=span, adjust=False).mean()


def compute_all(df: pd.DataFrame) -> dict:
    c, h, l = df["Close"], df["High"], df["Low"]

    macd_line, macd_sig, macd_hist = macd(c)
    adx_val, plus_di, minus_di     = adx(h, l, c)
    bb_upper, bb_mid, bb_lower     = bollinger(c)
    stoch_k, stoch_d               = stochastic(h, l, c)

    return {
        "rsi":        rsi(c),
        "macd_line":  macd_line,
        "macd_signal": macd_sig,
        "macd_hist":  macd_hist,
        "atr":        atr(h, l, c),
        "adx":        adx_val,
        "plus_di":    plus_di,
        "minus_di":   minus_di,
        "bb_upper":   bb_upper,
        "bb_mid":     bb_mid,
        "bb_lower":   bb_lower,
        "stoch_k":    stoch_k,
        "stoch_d":    stoch_d,
        "ema20":      ema(c, 20),
        "ema50":      ema(c, 50),
        "ema200":     ema(c, 200),
    }
