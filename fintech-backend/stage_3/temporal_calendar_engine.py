# =====================================================
# ENGINE 3.T1 — TEMPORAL CALENDAR ENGINE
# =====================================================
# Generates the master timestamp sequence that drives
# all temporal logic. Business-calendar-aware with
# holiday calendars, intraday patterns, and Poisson
# jitter for realistic irregular spacing.
#
# Pure NumPy + datetime. No external dependencies.
# =====================================================

import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional


# ─────────────────────────────────────────────────
# HOLIDAY QUICK-LOOKUP (month, day) tuples
# ─────────────────────────────────────────────────

def _build_holiday_set(holidays: List[Tuple[int, int]], years: List[int]) -> set:
    """Build a set of (year, month, day) tuples for fast lookup."""
    result = set()
    for year in years:
        for month, day in holidays:
            try:
                # Validate the date is real
                datetime(year, month, day)
                result.add((year, month, day))
            except ValueError:
                pass
    return result


# ─────────────────────────────────────────────────
# MAIN CALENDAR GENERATION
# ─────────────────────────────────────────────────

def generate_temporal_grid(
    temporal_model: Dict[str, Any],
    n_rows: int,
    rng: np.random.Generator,
    region: str = "US",
) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    """
    Generate the master timestamp grid for time-series generation.

    This is the backbone of H2 — every other temporal engine uses
    the timestamps produced here.

    Args:
        temporal_model: Compiled temporal model from Stage 2
        n_rows:         Target number of rows (may adjust to match calendar)
        rng:            Seeded RNG from seed engine
        region:         Region code for holiday calendar

    Returns:
        timestamps:      np.ndarray of ISO datetime strings
        time_index:      np.ndarray of float (fractional periods from start)
        calendar_meta:   Dict with auxiliary arrays:
                         - day_of_week: np.ndarray of int (0=Mon, 6=Sun)
                         - month: np.ndarray of int (1-12)
                         - quarter: np.ndarray of int (1-4)
                         - is_holiday: np.ndarray of bool
                         - is_month_end: np.ndarray of bool
                         - is_quarter_end: np.ndarray of bool
                         - seasonal_factor: np.ndarray of float
    """
    calendar_config = temporal_model.get("calendar", {})
    seasonal_config = temporal_model.get("seasonal", {})
    frequency = calendar_config.get("frequency", "monthly")
    periods = calendar_config.get("periods", n_rows)
    start_date_str = calendar_config.get("start_date", "2024-01-01")
    end_date_str = calendar_config.get("end_date", "2025-12-31")
    holidays = calendar_config.get("holidays", [])
    weekend_days = calendar_config.get("weekend_days", [5, 6])
    skip_holidays = calendar_config.get("skip_holidays", True)
    includes_weekends = calendar_config.get("includes_weekends", False)

    # ── Parse date range ──
    try:
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        start_dt = datetime(2024, 1, 1)

    try:
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        end_dt = datetime(2025, 12, 31)

    if end_dt <= start_dt:
        end_dt = start_dt + timedelta(days=365)

    # ── Generate raw date grid based on frequency ──
    if frequency == "daily":
        dates = _generate_daily_grid(
            start_dt, end_dt, periods, holidays, weekend_days,
            skip_holidays, includes_weekends, rng,
        )
    elif frequency == "weekly":
        dates = _generate_weekly_grid(start_dt, end_dt, periods)
    elif frequency == "monthly":
        dates = _generate_monthly_grid(start_dt, end_dt, periods)
    elif frequency == "quarterly":
        dates = _generate_quarterly_grid(start_dt, end_dt, periods)
    elif frequency == "yearly":
        dates = _generate_yearly_grid(start_dt, end_dt, periods)
    else:
        dates = _generate_monthly_grid(start_dt, end_dt, periods)

    # Ensure we have at least 3 dates
    if len(dates) < 3:
        dates = _generate_monthly_grid(start_dt, start_dt + timedelta(days=180), 6)

    n_actual = len(dates)

    # ── Build calendar metadata arrays ──
    day_of_week = np.array([d.weekday() for d in dates], dtype=int)
    month = np.array([d.month for d in dates], dtype=int)
    quarter = np.array([(d.month - 1) // 3 + 1 for d in dates], dtype=int)
    year = np.array([d.year for d in dates], dtype=int)

    # Holiday detection
    unique_years = list(set(y for y in year))
    holiday_set = _build_holiday_set(holidays, unique_years)
    is_holiday = np.array([(d.year, d.month, d.day) in holiday_set for d in dates], dtype=bool)

    # Month-end and quarter-end flags
    is_month_end = np.zeros(n_actual, dtype=bool)
    is_quarter_end = np.zeros(n_actual, dtype=bool)
    for i in range(n_actual):
        if i < n_actual - 1:
            is_month_end[i] = dates[i].month != dates[i + 1].month
            is_quarter_end[i] = quarter[i] != quarter[min(i + 1, n_actual - 1)]
        else:
            is_month_end[i] = True
            is_quarter_end[i] = True

    # ── Compute seasonal factors ──
    seasonal_factor = _compute_seasonal_factors(
        dates, day_of_week, month, is_holiday,
        seasonal_config, frequency,
    )

    # ── Time index (fractional periods from start) ──
    if n_actual > 1:
        total_seconds = (dates[-1] - dates[0]).total_seconds()
        if total_seconds > 0:
            time_index = np.array(
                [(d - dates[0]).total_seconds() / total_seconds * (n_actual - 1)
                 for d in dates],
                dtype=float,
            )
        else:
            time_index = np.arange(n_actual, dtype=float)
    else:
        time_index = np.array([0.0])

    # ── Format timestamps as ISO strings ──
    # Add intraday times for daily frequency with trading hours
    if frequency == "daily" and calendar_config.get("trading_hours"):
        timestamps = _add_intraday_times(dates, calendar_config["trading_hours"], rng)
    else:
        timestamps = np.array(
            [d.strftime("%Y-%m-%d %H:%M:%S") for d in dates],
            dtype=object,
        )

    calendar_meta = {
        "day_of_week": day_of_week,
        "month": month,
        "quarter": quarter,
        "year": year,
        "is_holiday": is_holiday,
        "is_month_end": is_month_end,
        "is_quarter_end": is_quarter_end,
        "seasonal_factor": seasonal_factor,
        "n_actual": n_actual,
    }

    return timestamps, time_index, calendar_meta


# ─────────────────────────────────────────────────
# GRID GENERATORS (per frequency)
# ─────────────────────────────────────────────────

def _generate_daily_grid(
    start: datetime,
    end: datetime,
    target_periods: int,
    holidays: List[Tuple[int, int]],
    weekend_days: List[int],
    skip_holidays: bool,
    includes_weekends: bool,
    rng: np.random.Generator,
) -> List[datetime]:
    """Generate a daily grid respecting business day rules."""
    unique_years = list(range(start.year, end.year + 2))
    holiday_set = _build_holiday_set(holidays, unique_years)

    dates = []
    current = start
    max_iterations = target_periods * 3  # Safety cap

    iteration = 0
    while len(dates) < target_periods and iteration < max_iterations:
        iteration += 1

        # Check if this date is valid
        is_weekend = current.weekday() in weekend_days
        is_hol = (current.year, current.month, current.day) in holiday_set

        valid = True
        if not includes_weekends and is_weekend:
            valid = False
        if skip_holidays and is_hol:
            valid = False

        if valid:
            dates.append(current)

        current += timedelta(days=1)

        if current > end + timedelta(days=365):
            break

    return dates[:target_periods]


def _generate_weekly_grid(
    start: datetime,
    end: datetime,
    target_periods: int,
) -> List[datetime]:
    """Generate weekly dates (every Monday or nearest business day)."""
    dates = []
    # Start from the next Monday
    current = start
    days_until_monday = (7 - current.weekday()) % 7
    current += timedelta(days=days_until_monday)

    while len(dates) < target_periods:
        dates.append(current)
        current += timedelta(weeks=1)
        if current > end + timedelta(days=365):
            break

    # If we didn't get enough dates, extend past end
    while len(dates) < target_periods:
        dates.append(current)
        current += timedelta(weeks=1)

    return dates[:target_periods]


def _generate_monthly_grid(
    start: datetime,
    end: datetime,
    target_periods: int,
) -> List[datetime]:
    """Generate month-end or mid-month dates."""
    dates = []
    year = start.year
    month = start.month

    while len(dates) < target_periods:
        # Use the 15th of each month (mid-month) for stability
        try:
            dt = datetime(year, month, 15)
            dates.append(dt)
        except ValueError:
            pass

        month += 1
        if month > 12:
            month = 1
            year += 1

        if year > end.year + 10:
            break

    return dates[:target_periods]


def _generate_quarterly_grid(
    start: datetime,
    end: datetime,
    target_periods: int,
) -> List[datetime]:
    """Generate quarter-end dates (March 31, June 30, Sep 30, Dec 31)."""
    quarter_ends = [(3, 31), (6, 30), (9, 30), (12, 31)]
    dates = []
    year = start.year
    qi = 0

    # Find the first quarter-end on or after start
    for i, (m, d) in enumerate(quarter_ends):
        if datetime(year, m, d) >= start:
            qi = i
            break
    else:
        year += 1
        qi = 0

    while len(dates) < target_periods:
        m, d = quarter_ends[qi]
        try:
            dates.append(datetime(year, m, d))
        except ValueError:
            pass

        qi += 1
        if qi >= 4:
            qi = 0
            year += 1

        if year > end.year + 20:
            break

    return dates[:target_periods]


def _generate_yearly_grid(
    start: datetime,
    end: datetime,
    target_periods: int,
) -> List[datetime]:
    """Generate year-end dates (December 31)."""
    dates = []
    year = start.year

    while len(dates) < target_periods:
        dates.append(datetime(year, 12, 31))
        year += 1
        if year > end.year + 50:
            break

    return dates[:target_periods]


# ─────────────────────────────────────────────────
# SEASONAL FACTOR COMPUTATION
# ─────────────────────────────────────────────────

def _compute_seasonal_factors(
    dates: List[datetime],
    day_of_week: np.ndarray,
    month: np.ndarray,
    is_holiday: np.ndarray,
    seasonal_config: Dict[str, Any],
    frequency: str,
) -> np.ndarray:
    """
    Compute multiplicative seasonal factors for each timestamp.

    seasonal_factor = month_factor × day_of_week_factor × holiday_factor
    """
    n = len(dates)
    factors = np.ones(n, dtype=float)

    month_factors = seasonal_config.get("month_factors", {})
    dow_factors = seasonal_config.get("day_of_week_factors", {})
    holiday_mult = seasonal_config.get("holiday_proximity_mult", 1.20)
    proximity_days = seasonal_config.get("holiday_proximity_days", 3)

    # Month-of-year effect
    for i in range(n):
        m_factor = month_factors.get(int(month[i]), 1.0)
        factors[i] *= m_factor

    # Day-of-week effect (only for daily/weekly)
    if frequency in ("daily", "weekly"):
        for i in range(n):
            dow_factor = dow_factors.get(int(day_of_week[i]), 1.0)
            factors[i] *= dow_factor

    # Holiday proximity effect
    # Dates near holidays get a boost (pre-holiday spending, etc.)
    if holiday_mult != 1.0 and proximity_days > 0:
        for i in range(n):
            if is_holiday[i]:
                # On the holiday itself
                factors[i] *= holiday_mult
            else:
                # Check proximity to nearest holiday
                for delta in range(1, proximity_days + 1):
                    left_idx = max(0, i - delta)
                    right_idx = min(n - 1, i + delta)
                    if is_holiday[left_idx] or is_holiday[right_idx]:
                        proximity_effect = 1.0 + (holiday_mult - 1.0) * (1.0 - delta / (proximity_days + 1))
                        factors[i] *= proximity_effect
                        break

    # Normalize: ensure mean factor ≈ 1.0 so seasonal effects
    # don't systematically inflate or deflate the data
    mean_factor = np.mean(factors)
    if mean_factor > 0:
        factors /= mean_factor

    return factors


# ─────────────────────────────────────────────────
# INTRADAY TIME ASSIGNMENT
# ─────────────────────────────────────────────────

def _add_intraday_times(
    dates: List[datetime],
    trading_hours: Tuple[int, int, int, int],
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Add realistic intraday timestamps within trading hours.
    Uses a bimodal distribution (more activity at open and close).
    """
    open_h, open_m, close_h, close_m = trading_hours
    open_minutes = open_h * 60 + open_m
    close_minutes = close_h * 60 + close_m
    trading_minutes = max(1, close_minutes - open_minutes)

    timestamps = []
    for d in dates:
        # Bimodal: mix of early-session and late-session times
        if rng.random() < 0.3:
            # Opening cluster (first 20% of session)
            offset = rng.integers(0, int(trading_minutes * 0.2))
        elif rng.random() < 0.4:
            # Closing cluster (last 20% of session)
            offset = rng.integers(int(trading_minutes * 0.8), trading_minutes)
        else:
            # Uniform across the session
            offset = rng.integers(0, trading_minutes)

        total_minutes = open_minutes + int(offset)
        hour = total_minutes // 60
        minute = total_minutes % 60
        second = int(rng.integers(0, 60))

        dt = d.replace(hour=hour, minute=minute, second=second)
        timestamps.append(dt.strftime("%Y-%m-%d %H:%M:%S"))

    return np.array(timestamps, dtype=object)
