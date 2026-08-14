# =====================================================
# TEMPORAL INTENT EXTRACTOR — Horizon 2
# =====================================================
# Extracts time-series intent from natural language
# prompts. Keyword-first approach consistent with the
# existing Stage 1 intent extraction pattern.
#
# Extracts:
#   - frequency: daily, weekly, monthly, quarterly, yearly
#   - time_horizon: number of periods or date range
#   - temporal_pattern: trending, seasonal, regime_shift, etc.
#   - regime_hint: crisis, bull_market, recession, etc.
#   - start_date / end_date: explicit or inferred
#
# NEVER throws. Returns None if no temporal intent found.
# =====================================================

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────
# KEYWORD DICTIONARIES
# ─────────────────────────────────────────────────

FREQUENCY_KEYWORDS = {
    "daily": ["daily", "per day", "each day", "every day", "day-by-day", "day by day", "intraday"],
    "weekly": ["weekly", "per week", "each week", "every week", "week-by-week", "week over week"],
    "monthly": ["monthly", "per month", "each month", "every month", "month-by-month", "month over month", "mom"],
    "quarterly": ["quarterly", "per quarter", "each quarter", "every quarter", "quarter-by-quarter", "qoq", "q1", "q2", "q3", "q4"],
    "yearly": ["yearly", "annually", "per year", "each year", "every year", "year-by-year", "year over year", "yoy", "annual"],
}

HORIZON_PATTERNS = [
    # "for 3 years", "over 2 years", "spanning 5 months"
    (r"(?:for|over|spanning|covering|across)\s+(\d+)\s+(year|month|week|day|quarter)s?", None),
    # "3-year", "12-month", "52-week"
    (r"(\d+)[\-\s]?(year|month|week|day|quarter)(?:s|ly)?", None),
    # "2024 to 2026", "2023-2025"
    (r"(20\d{2})\s*(?:to|through|thru|-)\s*(20\d{2})", "year_range"),
    # "Q4 2024", "Q1-Q4 2025"
    (r"Q([1-4])\s*(20\d{2})", "quarter_specific"),
    # "Q1-Q4", "Q2 to Q4"
    (r"Q([1-4])\s*(?:to|through|-)\s*Q([1-4])\s*(20\d{2})?", "quarter_range"),
    # "January 2024 to March 2025"
    (r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(20\d{2})\s+(?:to|through)\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(20\d{2})", "month_range"),
    # "last 6 months", "past 2 years", "recent 3 weeks"
    (r"(?:last|past|recent|previous)\s+(\d+)\s+(year|month|week|day|quarter)s?", "lookback"),
    # "next 12 months", "coming 5 years"
    (r"(?:next|coming|upcoming|future)\s+(\d+)\s+(year|month|week|day|quarter)s?", "forward"),
]

TEMPORAL_PATTERN_KEYWORDS = {
    "trending_up": ["trending up", "upward trend", "growing", "increasing", "rising", "bull", "bullish", "growth"],
    "trending_down": ["trending down", "downward trend", "declining", "decreasing", "falling", "bear", "bearish", "contraction"],
    "seasonal": ["seasonal", "seasonality", "cyclical", "cyclic", "periodic", "recurring pattern"],
    "regime_shift": ["regime shift", "regime change", "structural break", "phase transition", "market shift"],
    "mean_reverting": ["mean reverting", "mean reversion", "oscillating", "reverting to mean", "stable"],
    "random_walk": ["random walk", "brownian", "stochastic", "unpredictable"],
    "volatile": ["volatile", "volatility", "high variance", "turbulent", "chaotic", "wild swings"],
    "exponential_growth": ["exponential", "compound growth", "hockey stick", "parabolic", "hypergrowth"],
}

REGIME_HINT_KEYWORDS = {
    "crisis": ["crisis", "crash", "collapse", "meltdown", "panic", "black swan", "flash crash", "market crash"],
    "bull_market": ["bull market", "bull run", "rally", "boom", "euphoria", "all time high", "ath"],
    "recession": ["recession", "downturn", "contraction", "slowdown", "depression", "stagnation"],
    "recovery": ["recovery", "rebound", "bounce back", "turnaround", "normalization"],
    "stable": ["stable", "steady", "consistent", "flat", "sideways", "range-bound"],
    "bubble": ["bubble", "speculative", "frothy", "overheated", "irrational exuberance"],
}

MONTH_NAME_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# How many base periods each frequency unit represents
FREQUENCY_PERIODS = {
    "daily": {"day": 1, "week": 5, "month": 21, "quarter": 63, "year": 252},
    "weekly": {"day": 1, "week": 1, "month": 4, "quarter": 13, "year": 52},
    "monthly": {"day": 1, "week": 1, "month": 1, "quarter": 3, "year": 12},
    "quarterly": {"day": 1, "week": 1, "month": 1, "quarter": 1, "year": 4},
    "yearly": {"day": 1, "week": 1, "month": 1, "quarter": 1, "year": 1},
}


# ─────────────────────────────────────────────────
# MAIN EXTRACTION FUNCTION
# ─────────────────────────────────────────────────

def extract_temporal_intent(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Extract temporal / time-series intent from a prompt string.

    Returns None if no temporal signals are detected (meaning the
    pipeline should use the static H1 generation path).

    Returns a temporal intent dict if temporal signals are found:
    {
        "is_temporal": True,
        "frequency": "monthly",
        "periods": 24,
        "start_date": "2024-01-01",
        "end_date": "2025-12-31",
        "temporal_pattern": "seasonal",
        "regime_hint": None,
        "raw_horizon": "2 years",
        "confidence": 0.85,
    }
    """
    if not prompt or not isinstance(prompt, str):
        return None

    prompt_lower = prompt.lower().strip()

    # ── Extract each temporal component ──
    frequency = _extract_frequency(prompt_lower)
    horizon_result = _extract_horizon(prompt_lower)
    pattern = _extract_temporal_pattern(prompt_lower)
    regime = _extract_regime_hint(prompt_lower)

    # ── Determine if this is a temporal prompt ──
    # Must have at least ONE strong temporal signal
    has_frequency = frequency is not None
    has_horizon = horizon_result is not None
    has_pattern = pattern is not None
    has_regime = regime is not None

    signal_count = sum([has_frequency, has_horizon, has_pattern, has_regime])

    if signal_count == 0:
        # No temporal signals at all — use static path
        return None

    # ── Resolve dates and periods ──
    if frequency is None:
        # Default frequency based on pattern or horizon
        frequency = "monthly"

    start_date = None
    end_date = None
    periods = None
    raw_horizon = None

    if horizon_result:
        start_date = horizon_result.get("start_date")
        end_date = horizon_result.get("end_date")
        periods = horizon_result.get("periods")
        raw_horizon = horizon_result.get("raw")

        # If we got a date range but no period count, calculate it
        if start_date and end_date and not periods:
            periods = _calculate_periods(start_date, end_date, frequency)

        # If we got _count and _unit (e.g., "2 years"), convert to periods
        if periods is None and "_count" in horizon_result and "_unit" in horizon_result:
            h_count = horizon_result["_count"]
            h_unit = horizon_result["_unit"]
            freq_map = FREQUENCY_PERIODS.get(frequency, {})
            periods_per_unit = freq_map.get(h_unit, 1)
            periods = h_count * periods_per_unit

    # ── Default periods if still None ──
    if periods is None:
        # Smart defaults based on frequency
        default_periods = {
            "daily": 252,       # ~1 trading year
            "weekly": 52,       # 1 year
            "monthly": 24,      # 2 years
            "quarterly": 12,    # 3 years
            "yearly": 5,        # 5 years
        }
        periods = default_periods.get(frequency, 24)

    # Sanity clamp: don't generate absurd period counts
    periods = max(3, min(periods, 2520))  # 3 minimum, ~10 years daily max

    # ── Calculate dates if not explicitly provided ──
    if not start_date and not end_date:
        # Default: end at "now" (2025-12-31 for reproducibility), work backward
        end_date = "2025-12-31"
        start_date = _subtract_periods(end_date, frequency, periods)

    # ── Confidence scoring ──
    confidence = min(1.0, signal_count * 0.35)
    if has_frequency and has_horizon:
        confidence = max(confidence, 0.80)
    if has_frequency and has_horizon and (has_pattern or has_regime):
        confidence = 0.95

    temporal_intent = {
        "is_temporal": True,
        "frequency": frequency,
        "periods": int(periods),
        "start_date": start_date,
        "end_date": end_date,
        "temporal_pattern": pattern,
        "regime_hint": regime,
        "raw_horizon": raw_horizon,
        "confidence": round(confidence, 3),
    }

    print(f"\n[*] TEMPORAL INTENT DETECTED:")
    print(f"    Frequency: {frequency}")
    print(f"    Periods: {periods}")
    print(f"    Pattern: {pattern}")
    print(f"    Regime: {regime}")
    print(f"    Date range: {start_date} → {end_date}")
    print(f"    Confidence: {confidence:.3f}")

    return temporal_intent


# ─────────────────────────────────────────────────
# COMPONENT EXTRACTORS
# ─────────────────────────────────────────────────

def _extract_frequency(prompt: str) -> Optional[str]:
    """Extract the time-series frequency from keywords."""
    best_freq = None
    best_pos = len(prompt)  # Earliest match wins for tie-breaking

    for freq, keywords in FREQUENCY_KEYWORDS.items():
        for kw in keywords:
            pos = prompt.find(kw)
            if pos != -1 and pos < best_pos:
                best_freq = freq
                best_pos = pos

    return best_freq


def _extract_horizon(prompt: str) -> Optional[Dict[str, Any]]:
    """Extract the time horizon / date range from the prompt."""
    for pattern_str, pattern_type in HORIZON_PATTERNS:
        match = re.search(pattern_str, prompt, re.IGNORECASE)
        if not match:
            continue

        if pattern_type == "year_range":
            start_year = int(match.group(1))
            end_year = int(match.group(2))
            return {
                "start_date": f"{start_year}-01-01",
                "end_date": f"{end_year}-12-31",
                "periods": None,  # Will be calculated from frequency
                "raw": f"{start_year} to {end_year}",
            }

        elif pattern_type == "quarter_specific":
            quarter = int(match.group(1))
            year = int(match.group(2))
            q_start_month = (quarter - 1) * 3 + 1
            q_end_month = quarter * 3
            q_end_day = 31 if q_end_month in (3, 12) else 30
            return {
                "start_date": f"{year}-{q_start_month:02d}-01",
                "end_date": f"{year}-{q_end_month:02d}-{q_end_day:02d}",
                "periods": None,
                "raw": f"Q{quarter} {year}",
            }

        elif pattern_type == "quarter_range":
            q_start = int(match.group(1))
            q_end = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else 2025
            s_month = (q_start - 1) * 3 + 1
            e_month = q_end * 3
            e_day = 31 if e_month in (3, 12) else 30
            return {
                "start_date": f"{year}-{s_month:02d}-01",
                "end_date": f"{year}-{e_month:02d}-{e_day:02d}",
                "periods": None,
                "raw": f"Q{q_start}-Q{q_end} {year}",
            }

        elif pattern_type == "month_range":
            start_month_name = match.group(1).lower()
            start_year = int(match.group(2))
            end_month_name = match.group(3).lower()
            end_year = int(match.group(4))
            s_month = MONTH_NAME_MAP.get(start_month_name, 1)
            e_month = MONTH_NAME_MAP.get(end_month_name, 12)
            e_day = 31 if e_month in (1, 3, 5, 7, 8, 10, 12) else (28 if e_month == 2 else 30)
            return {
                "start_date": f"{start_year}-{s_month:02d}-01",
                "end_date": f"{end_year}-{e_month:02d}-{e_day:02d}",
                "periods": None,
                "raw": f"{match.group(1)} {start_year} to {match.group(3)} {end_year}",
            }

        elif pattern_type in ("lookback", "forward"):
            count = int(match.group(1))
            unit = match.group(2).lower()
            # Calculate periods based on unit
            period_map = {"day": 1, "week": 7, "month": 30, "quarter": 90, "year": 365}
            total_days = count * period_map.get(unit, 30)

            if pattern_type == "lookback":
                end_dt = datetime(2025, 12, 31)
                start_dt = end_dt - timedelta(days=total_days)
            else:
                start_dt = datetime(2025, 1, 1)
                end_dt = start_dt + timedelta(days=total_days)

            return {
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "periods": None,
                "raw": match.group(0),
            }

        else:
            # Standard "N unit" pattern
            count = int(match.group(1))
            unit = match.group(2).lower()
            return {
                "start_date": None,
                "end_date": None,
                "periods": None,  # Will be calculated in main function
                "raw": f"{count} {unit}s",
                "_count": count,
                "_unit": unit,
            }

    return None


def _extract_temporal_pattern(prompt: str) -> Optional[str]:
    """Extract temporal pattern (trending, seasonal, volatile, etc.)."""
    best_pattern = None
    best_count = 0

    for pattern, keywords in TEMPORAL_PATTERN_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in prompt)
        if count > best_count:
            best_count = count
            best_pattern = pattern

    return best_pattern


def _extract_regime_hint(prompt: str) -> Optional[str]:
    """Extract regime hints (crisis, bull market, recession, etc.)."""
    best_regime = None
    best_count = 0

    for regime, keywords in REGIME_HINT_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in prompt)
        if count > best_count:
            best_count = count
            best_regime = regime

    return best_regime


# ─────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────

def _calculate_periods(start_date: str, end_date: str, frequency: str) -> int:
    """Calculate number of periods between two dates at a given frequency."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta_days = (end - start).days

        if delta_days <= 0:
            return 12  # fallback

        if frequency == "daily":
            # Approximate trading days (5/7 of calendar days)
            return max(3, int(delta_days * 5 / 7))
        elif frequency == "weekly":
            return max(3, delta_days // 7)
        elif frequency == "monthly":
            return max(3, delta_days // 30)
        elif frequency == "quarterly":
            return max(3, delta_days // 90)
        elif frequency == "yearly":
            return max(3, delta_days // 365)
        else:
            return max(3, delta_days // 30)
    except (ValueError, TypeError):
        return 12


def _subtract_periods(end_date_str: str, frequency: str, periods: int) -> str:
    """Calculate start date by subtracting N periods from end date."""
    try:
        end = datetime.strptime(end_date_str, "%Y-%m-%d")

        days_per_period = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365,
        }
        total_days = periods * days_per_period.get(frequency, 30)
        start = end - timedelta(days=total_days)
        return start.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return "2024-01-01"
