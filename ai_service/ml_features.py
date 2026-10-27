"""Shared ML features for training and inference.
The 21-observation window includes the current observation.
This is same-day detection, not future forecasting.
"""
from typing import List
import numpy as np


def build_causal_features(history_values: List[float], window_size: int = 21) -> np.ndarray:
    """
    Build 18 features from the latest 21 observations, including the current day.
    No observations after the current day may be supplied.
    """
    if len(history_values) < window_size:
        raise ValueError(f"Need at least {window_size} history values")

    hist = np.array(history_values[-window_size:], dtype=float)
    features = []

    median_hist = np.median(hist)
    mean_hist = np.mean(hist)
    std_hist = np.std(hist, ddof=0)
    mad_hist = np.median(np.abs(hist - median_hist))
    q25 = np.percentile(hist, 25)
    q75 = np.percentile(hist, 75)
    iqr = q75 - q25

    features.append(median_hist)
    features.append(mean_hist)
    features.append(std_hist)
    features.append(mad_hist)
    features.append(q25)
    features.append(q75)
    features.append(iqr)

    # Use last value as current (most recent in history)
    current = hist[-1]
    features.append(current)
    features.append(current - median_hist)
    features.append((current - median_hist) / (mad_hist * 1.4826 + 1e-8))
    features.append(current / (mean_hist + 1e-8))

    if len(hist) >= 14:
        last7 = hist[-7:]
        prev7 = hist[-14:-7]
        features.append(np.mean(last7))
        features.append(np.mean(last7) - np.mean(prev7))
        features.append(np.mean(last7) / (np.mean(prev7) + 1e-8))
    else:
        features.append(np.mean(hist[-min(7, len(hist)):]))
        features.append(0.0)
        features.append(1.0)

    if len(hist) >= 3:
        features.append(hist[-1] - hist[-2])
        features.append(hist[-1] - hist[-3])
    else:
        features.append(0.0)
        features.append(0.0)

    features.append(np.max(hist) - np.min(hist))
    features.append((hist[-1] - hist[0]) / len(hist))

    return np.array(features)


def get_feature_names():
    return [
        "median_hist", "mean_hist", "std_hist", "mad_hist", "q25", "q75", "iqr",
        "current", "current_minus_median", "robust_zscore", "current_over_mean",
        "mean_last7", "mean_last7_minus_prev7", "last7_over_prev7",
        "diff1", "diff2", "range_hist", "trend_slope"
    ]
