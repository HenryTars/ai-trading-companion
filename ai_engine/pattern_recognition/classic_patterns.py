import numpy as np
import pandas as pd
from typing import List, Dict


def _pivot_highs(df: pd.DataFrame, left: int = 5, right: int = 5) -> List[int]:
    highs = df["High"].values
    pivots = []
    for i in range(left, len(highs) - right):
        if highs[i] == max(highs[i - left: i + right + 1]):
            pivots.append(i)
    return pivots


def _pivot_lows(df: pd.DataFrame, left: int = 5, right: int = 5) -> List[int]:
    lows = df["Low"].values
    pivots = []
    for i in range(left, len(lows) - right):
        if lows[i] == min(lows[i - left: i + right + 1]):
            pivots.append(i)
    return pivots


def _pct(a, b) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-10)


# ── Head & Shoulders ──────────────────────────────────────────────────────────

def _head_and_shoulders(df: pd.DataFrame) -> List[Dict]:
    patterns = []
    ph = _pivot_highs(df, 4, 4)
    if len(ph) < 3:
        return patterns
    lows = df["Low"].values
    highs = df["High"].values
    for i in range(len(ph) - 2):
        L, H, R = ph[i], ph[i + 1], ph[i + 2]
        lh, hh, rh = highs[L], highs[H], highs[R]
        if hh <= lh or hh <= rh:
            continue
        if _pct(lh, rh) > 0.04:
            continue
        neck_l = min(lows[L:H + 1])
        neck_r = min(lows[H:R + 1])
        if _pct(neck_l, neck_r) > 0.04:
            continue
        patterns.append({"type": "Head & Shoulders", "index": R, "bias": "bearish",
                         "confidence": 0.75, "neckline": (neck_l + neck_r) / 2})
    return patterns


def _inverse_head_and_shoulders(df: pd.DataFrame) -> List[Dict]:
    patterns = []
    pl = _pivot_lows(df, 4, 4)
    if len(pl) < 3:
        return patterns
    highs = df["High"].values
    lows = df["Low"].values
    for i in range(len(pl) - 2):
        L, H, R = pl[i], pl[i + 1], pl[i + 2]
        ll, hl, rl = lows[L], lows[H], lows[R]
        if hl >= ll or hl >= rl:
            continue
        if _pct(ll, rl) > 0.04:
            continue
        neck_l = max(highs[L:H + 1])
        neck_r = max(highs[H:R + 1])
        if _pct(neck_l, neck_r) > 0.04:
            continue
        patterns.append({"type": "Inverse Head & Shoulders", "index": R, "bias": "bullish",
                         "confidence": 0.75, "neckline": (neck_l + neck_r) / 2})
    return patterns


# ── Double Top / Bottom ───────────────────────────────────────────────────────

def _double_top(df: pd.DataFrame) -> List[Dict]:
    patterns = []
    ph = _pivot_highs(df, 5, 5)
    highs = df["High"].values
    for i in range(len(ph) - 1):
        A, B = ph[i], ph[i + 1]
        if B - A < 8:
            continue
        if _pct(highs[A], highs[B]) > 0.015:
            continue
        patterns.append({"type": "Double Top", "index": B, "bias": "bearish", "confidence": 0.70})
    return patterns


def _double_bottom(df: pd.DataFrame) -> List[Dict]:
    patterns = []
    pl = _pivot_lows(df, 5, 5)
    lows = df["Low"].values
    for i in range(len(pl) - 1):
        A, B = pl[i], pl[i + 1]
        if B - A < 8:
            continue
        if _pct(lows[A], lows[B]) > 0.015:
            continue
        patterns.append({"type": "Double Bottom", "index": B, "bias": "bullish", "confidence": 0.70})
    return patterns


# ── Triangles ─────────────────────────────────────────────────────────────────

def _triangle(df: pd.DataFrame) -> List[Dict]:
    patterns = []
    close = df["Close"].values
    n = len(close)
    window = 30
    if n < window + 10:
        return patterns

    for start in range(n - window - 1, max(n - window * 2, 0), -10):
        end = start + window
        if end >= n:
            continue
        seg = close[start:end]
        x = np.arange(len(seg), dtype=float)
        ph_idx = [i for i in range(2, len(seg) - 2)
                  if seg[i] == max(seg[i - 2: i + 3])]
        pl_idx = [i for i in range(2, len(seg) - 2)
                  if seg[i] == min(seg[i - 2: i + 3])]
        if len(ph_idx) < 2 or len(pl_idx) < 2:
            continue

        h_slope = np.polyfit([ph_idx[0], ph_idx[-1]], [seg[ph_idx[0]], seg[ph_idx[-1]]], 1)[0]
        l_slope = np.polyfit([pl_idx[0], pl_idx[-1]], [seg[pl_idx[0]], seg[pl_idx[-1]]], 1)[0]

        label = None
        if h_slope < -0.001 and l_slope > 0.001:
            label, bias = "Symmetrical Triangle", "neutral"
        elif abs(h_slope) < 0.0005 and l_slope > 0.001:
            label, bias = "Ascending Triangle", "bullish"
        elif h_slope < -0.001 and abs(l_slope) < 0.0005:
            label, bias = "Descending Triangle", "bearish"

        if label:
            patterns.append({"type": label, "index": start + window - 1,
                              "bias": bias, "confidence": 0.65})
    return patterns


# ── Flags & Pennants ──────────────────────────────────────────────────────────

def _flags(df: pd.DataFrame) -> List[Dict]:
    patterns = []
    close = df["Close"].values
    n = len(close)
    pole = 12
    flag_len = 8
    if n < pole + flag_len + 5:
        return patterns

    for i in range(pole, n - flag_len - 2):
        pole_move = (close[i] - close[i - pole]) / max(abs(close[i - pole]), 1e-10)
        if abs(pole_move) < 0.03:
            continue
        seg = close[i: i + flag_len]
        slope = np.polyfit(np.arange(flag_len, dtype=float), seg, 1)[0]
        bullish_pole = pole_move > 0
        if bullish_pole and -0.002 < slope < 0:
            patterns.append({"type": "Bull Flag", "index": i + flag_len - 1,
                              "bias": "bullish", "confidence": 0.68})
        elif not bullish_pole and 0 < slope < 0.002:
            patterns.append({"type": "Bear Flag", "index": i + flag_len - 1,
                              "bias": "bearish", "confidence": 0.68})
    return patterns[-3:]


# ── Wedges ────────────────────────────────────────────────────────────────────

def _wedges(df: pd.DataFrame) -> List[Dict]:
    patterns = []
    close = df["High"].values
    low = df["Low"].values
    n = len(close)
    win = 25
    if n < win + 5:
        return patterns

    start = n - win - 1
    end = n - 1
    x = np.arange(win, dtype=float)
    h_seg = close[start:start + win]
    l_seg = low[start:start + win]
    h_slope = np.polyfit(x, h_seg, 1)[0]
    l_slope = np.polyfit(x, l_seg, 1)[0]

    if h_slope > 0.0001 and l_slope > 0.0001 and h_slope < l_slope:
        patterns.append({"type": "Rising Wedge", "index": end, "bias": "bearish", "confidence": 0.67})
    elif h_slope < -0.0001 and l_slope < -0.0001 and h_slope > l_slope:
        patterns.append({"type": "Falling Wedge", "index": end, "bias": "bullish", "confidence": 0.67})
    return patterns


# ── Public API ────────────────────────────────────────────────────────────────

def detect_classic_patterns(df: pd.DataFrame) -> List[Dict]:
    if df.empty or len(df) < 30:
        return []

    all_p: List[Dict] = []
    for fn in [_head_and_shoulders, _inverse_head_and_shoulders,
               _double_top, _double_bottom, _triangle, _flags, _wedges]:
        try:
            all_p.extend(fn(df))
        except Exception:
            pass

    seen: set = set()
    unique = []
    for p in sorted(all_p, key=lambda x: x["index"]):
        key = (p["type"], p["index"] // 5)
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique[-15:]
