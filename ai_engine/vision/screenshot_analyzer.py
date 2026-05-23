"""
Screenshot Vision Analyzer
Analyzes uploaded chart screenshots using OpenCV to detect:
- Trend direction and trend lines
- Support / resistance zones (color clustering)
- Candlestick-like bar structure
- Chart pattern hints
"""

import io
import numpy as np
from typing import Dict, List, Tuple


def _load_image(image_bytes: bytes):
    import cv2
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def _detect_trend_lines(gray: np.ndarray, img_h: int, img_w: int) -> Dict:
    import cv2
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi / 180,
                             threshold=80, minLineLength=img_w // 6,
                             maxLineGap=img_w // 20)

    if lines is None:
        return {"direction": "unclear", "up_lines": 0, "down_lines": 0, "total_lines": 0}

    up, down, flat = 0, 0, 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 == x1:
            continue
        slope = (y2 - y1) / (x2 - x1)
        if slope < -0.08:
            up += 1
        elif slope > 0.08:
            down += 1
        else:
            flat += 1

    total = up + down + flat
    if total == 0:
        direction = "unclear"
    elif up > down * 1.3:
        direction = "uptrend"
    elif down > up * 1.3:
        direction = "downtrend"
    else:
        direction = "ranging"

    return {"direction": direction, "up_lines": up, "down_lines": down,
            "flat_lines": flat, "total_lines": total}


def _detect_sr_zones(gray: np.ndarray, img_h: int) -> Dict:
    """Find horizontal S/R zones by detecting horizontal line clusters."""
    import cv2
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 20, 80)

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (img_h // 10, 1))
    h_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)

    row_sums = np.sum(h_lines, axis=1)
    threshold = max(row_sums.mean() + row_sums.std(), 1)

    candidate_rows = np.where(row_sums > threshold)[0]

    if len(candidate_rows) == 0:
        return {"zones": [], "support_count": 0, "resistance_count": 0}

    # Cluster rows within 5px of each other
    zones = []
    cluster = [candidate_rows[0]]
    for r in candidate_rows[1:]:
        if r - cluster[-1] <= 5:
            cluster.append(r)
        else:
            zones.append(int(np.mean(cluster)))
            cluster = [r]
    zones.append(int(np.mean(cluster)))

    mid = img_h // 2
    support = [z for z in zones if z > mid]
    resistance = [z for z in zones if z <= mid]

    return {"zones": zones, "support_count": len(support), "resistance_count": len(resistance)}


def _detect_candle_structure(img_bgr: np.ndarray) -> Dict:
    """
    Estimate bullish/bearish candle dominance by comparing
    green vs red pixel area in the chart body region.
    """
    import cv2
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255]))
    red_mask1  = cv2.inRange(hsv, np.array([0,  40, 40]), np.array([10, 255, 255]))
    red_mask2  = cv2.inRange(hsv, np.array([160, 40, 40]), np.array([180, 255, 255]))
    red_mask   = cv2.bitwise_or(red_mask1, red_mask2)

    green_px = int(np.sum(green_mask > 0))
    red_px   = int(np.sum(red_mask > 0))
    total    = green_px + red_px

    if total == 0:
        sentiment = "neutral"
        green_pct = red_pct = 50
    else:
        green_pct = round(green_px / total * 100, 1)
        red_pct   = round(red_px   / total * 100, 1)
        if green_pct > 58:
            sentiment = "bullish"
        elif red_pct > 58:
            sentiment = "bearish"
        else:
            sentiment = "mixed"

    return {"sentiment": sentiment, "bullish_pct": green_pct, "bearish_pct": red_pct}


def _detect_patterns_visual(trend_dir: str, sr: Dict, candle: Dict) -> List[str]:
    hints = []
    if trend_dir == "uptrend" and candle["sentiment"] == "bullish":
        hints.append("Strong uptrend — bullish candle dominance confirms momentum")
    elif trend_dir == "downtrend" and candle["sentiment"] == "bearish":
        hints.append("Strong downtrend — bearish candle dominance confirms momentum")
    elif trend_dir in ("uptrend", "downtrend") and candle["sentiment"] == "mixed":
        hints.append(f"Trend lines suggest {trend_dir} but candle colors show indecision — possible reversal area")
    elif trend_dir == "ranging":
        hints.append("Chart shows ranging / consolidation structure")

    if sr["resistance_count"] >= 2:
        hints.append(f"{sr['resistance_count']} resistance zones detected in upper chart region")
    if sr["support_count"] >= 2:
        hints.append(f"{sr['support_count']} support zones detected in lower chart region")

    if sr["support_count"] >= 2 and sr["resistance_count"] >= 2:
        hints.append("Multiple S/R levels visible — watch for breakout or bounce")

    return hints


def _annotate_image(img_bgr: np.ndarray, trend: Dict, sr: Dict) -> bytes:
    """Draw trend direction label and S/R zones on the image; return as PNG bytes."""
    import cv2
    annotated = img_bgr.copy()
    h, w = annotated.shape[:2]

    label_colors = {"uptrend": (0, 200, 80), "downtrend": (60, 60, 220), "ranging": (30, 180, 220), "unclear": (150, 150, 150)}
    color = label_colors.get(trend["direction"], (200, 200, 200))
    cv2.putText(annotated, f"Trend: {trend['direction'].upper()}", (12, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

    mid = h // 2
    for y in sr.get("zones", []):
        zone_color = (60, 60, 220) if y <= mid else (0, 180, 80)
        cv2.line(annotated, (0, y), (w, y), zone_color, 1)

    _, buf = cv2.imencode(".png", annotated)
    return buf.tobytes()


def analyze_screenshot(image_bytes: bytes) -> Dict:
    """
    Main entry point.
    Returns a dict with trend, sr_zones, candle_sentiment, pattern_hints,
    confidence, bias, and annotated_image_bytes (PNG).
    """
    try:
        import cv2
        img = _load_image(image_bytes)
        if img is None:
            return {"error": "Could not decode image. Please upload a valid PNG or JPG."}

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        trend   = _detect_trend_lines(gray, h, w)
        sr      = _detect_sr_zones(gray, h)
        candle  = _detect_candle_structure(img)
        hints   = _detect_patterns_visual(trend["direction"], sr, candle)
        annotated = _annotate_image(img, trend, sr)

        # Derive overall bias
        votes = {"bullish": 0, "bearish": 0, "neutral": 0}
        if trend["direction"] == "uptrend":   votes["bullish"] += 2
        if trend["direction"] == "downtrend": votes["bearish"] += 2
        if candle["sentiment"] == "bullish":  votes["bullish"] += 1
        if candle["sentiment"] == "bearish":  votes["bearish"] += 1

        bias = max(votes, key=lambda k: votes[k])
        if votes["bullish"] == votes["bearish"]:
            bias = "neutral"

        conf_score = min(95, 40 + trend["total_lines"] * 2 + sr["zones"].__len__() * 3)

        return {
            "bias": bias,
            "confidence": conf_score,
            "trend": trend,
            "sr_zones": sr,
            "candle_structure": candle,
            "pattern_hints": hints,
            "annotated_image": annotated,
        }

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}
