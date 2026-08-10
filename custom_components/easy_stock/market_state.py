"""Derive the exchange session state from a Yahoo Finance chart response.

Yahoo dropped ``meta.marketState`` from the v8 chart API, which left the
integration reporting a hardcoded "CLOSED" for every symbol (issue #13). The
``meta.currentTradingPeriod`` object is still served and carries the pre,
regular and post windows as epoch seconds, so the session state is derived
from those instead.
"""
from datetime import datetime, timezone

# A window covering (near enough) a full day means the asset trades
# continuously — crypto reports 00:00–23:59 UTC, and the resulting one minute
# before midnight is a rollover artefact, not a close.
_CONTINUOUS_SPAN = 86340  # 23 h 59 min

# FX pairs carry the same 24 h window as crypto but rest from Friday 22:00 to
# Sunday 22:00 UTC, and the window alone cannot tell the two apart. A pair that
# is genuinely trading ticks within seconds, so a last trade this old means the
# market is resting. Generous enough to absorb a quiet pair or a lagging feed.
_CONTINUOUS_STALE_AFTER = 7200  # 2 h


def _bounds(period: dict, name: str) -> tuple[int, int] | None:
    """Return the (start, end) epoch pair of a window, or None if unusable."""
    window = period.get(name)
    if not isinstance(window, dict):
        return None
    start, end = window.get("start"), window.get("end")
    if not isinstance(start, int) or not isinstance(end, int) or end <= start:
        return None
    return start, end


def derive_market_state(meta: dict, now: int | None = None) -> str | None:
    """Return "REGULAR", "PRE", "POST" or "CLOSED" for the given chart meta.

    Returns None when Yahoo ships neither an explicit state nor usable trading
    windows, so the caller can fall back to its own heuristic instead of
    reporting a session state that was never measured.
    """
    explicit = meta.get("marketState")
    if isinstance(explicit, str) and explicit:
        return explicit

    period = meta.get("currentTradingPeriod")
    if not isinstance(period, dict):
        return None

    windows = {
        name: bounds
        for name in ("regular", "pre", "post")
        if (bounds := _bounds(period, name)) is not None
    }
    if not windows:
        return None

    if now is None:
        now = int(datetime.now(timezone.utc).timestamp())

    regular = windows.get("regular")
    if regular and regular[1] - regular[0] >= _CONTINUOUS_SPAN:
        last_tick = meta.get("regularMarketTime")
        if not isinstance(last_tick, int) or now - last_tick <= _CONTINUOUS_STALE_AFTER:
            return "REGULAR"
        return "CLOSED"

    # Yahoo reports adjacent windows (pre.end == regular.start); checking
    # regular first keeps the boundary on the side that matters.
    for name, state in (("regular", "REGULAR"), ("pre", "PRE"), ("post", "POST")):
        bounds = windows.get(name)
        if bounds and bounds[0] <= now < bounds[1]:
            return state

    return "CLOSED"
