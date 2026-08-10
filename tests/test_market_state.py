"""Unit tests for deriving the market state from Yahoo's currentTradingPeriod.

Yahoo removed ``meta.marketState`` from the v8 chart API (issue #13), so the
session status has to be reconstructed from ``meta.currentTradingPeriod``,
which still carries the pre/regular/post epoch windows.
"""
from custom_components.easy_stock.market_state import derive_market_state


def _meta(pre=None, regular=None, post=None, **extra):
    """Build a meta dict with the trading windows Yahoo actually ships."""
    period = {}
    if pre:
        period["pre"] = {"start": pre[0], "end": pre[1]}
    if regular:
        period["regular"] = {"start": regular[0], "end": regular[1]}
    if post:
        period["post"] = {"start": post[0], "end": post[1]}
    meta = {"currentTradingPeriod": period} if period else {}
    meta.update(extra)
    return meta


# Xetra on 2026-08-10: 07:00–15:30 UTC
XETRA_OPEN = 1786345200
XETRA_CLOSE = 1786375800

# NYSE on 2026-08-10: pre 12:00, regular 13:30–20:00, post 20:00–24:00 UTC
NYSE_PRE_START = 1786348800
NYSE_OPEN = 1786368600
NYSE_CLOSE = 1786392000
NYSE_POST_END = 1786406400


def test_regular_session_while_inside_the_window():
    meta = _meta(regular=(XETRA_OPEN, XETRA_CLOSE))
    assert derive_market_state(meta, now=XETRA_OPEN + 3600) == "REGULAR"


def test_closed_after_the_session_ended_on_the_same_day():
    """The Tokyo/Hongkong case: session over, but still the same UTC day."""
    meta = _meta(regular=(XETRA_OPEN, XETRA_CLOSE))
    assert derive_market_state(meta, now=XETRA_CLOSE + 60) == "CLOSED"


def test_closed_before_the_session_starts():
    meta = _meta(regular=(XETRA_OPEN, XETRA_CLOSE))
    assert derive_market_state(meta, now=XETRA_OPEN - 60) == "CLOSED"


def test_pre_market_window():
    meta = _meta(
        pre=(NYSE_PRE_START, NYSE_OPEN),
        regular=(NYSE_OPEN, NYSE_CLOSE),
        post=(NYSE_CLOSE, NYSE_POST_END),
    )
    assert derive_market_state(meta, now=NYSE_PRE_START + 60) == "PRE"


def test_post_market_window():
    meta = _meta(
        pre=(NYSE_PRE_START, NYSE_OPEN),
        regular=(NYSE_OPEN, NYSE_CLOSE),
        post=(NYSE_CLOSE, NYSE_POST_END),
    )
    assert derive_market_state(meta, now=NYSE_CLOSE + 60) == "POST"


def test_regular_wins_over_an_overlapping_pre_window():
    """Yahoo reports pre.end == regular.start; the boundary belongs to regular."""
    meta = _meta(
        pre=(NYSE_PRE_START, NYSE_OPEN),
        regular=(NYSE_OPEN, NYSE_CLOSE),
    )
    assert derive_market_state(meta, now=NYSE_OPEN) == "REGULAR"


def test_continuously_traded_asset_stays_open_in_the_midnight_gap():
    """Crypto reports regular as 00:00–23:59 UTC — the last minute is not a close."""
    day_start = 1786320000
    meta = _meta(regular=(day_start, day_start + 86340))  # 23:59
    assert derive_market_state(meta, now=day_start + 86370) == "REGULAR"


def test_continuous_window_goes_closed_once_the_ticks_stop():
    """FX reports a 24 h window too, but rests from Fri 22:00 to Sun 22:00 UTC.

    Only a stale regularMarketTime separates a resting FX pair from crypto, which
    keeps ticking through the weekend on an identically shaped window.
    """
    day_start = 1786320000
    now = day_start + 40000
    meta = _meta(
        regular=(day_start, day_start + 86340),
        regularMarketTime=now - 48 * 3600,  # last tick two days ago
    )
    assert derive_market_state(meta, now=now) == "CLOSED"


def test_continuous_window_stays_open_while_ticks_arrive():
    day_start = 1786320000
    now = day_start + 40000
    meta = _meta(
        regular=(day_start, day_start + 86340),
        regularMarketTime=now - 30,
    )
    assert derive_market_state(meta, now=now) == "REGULAR"


def test_returns_none_when_yahoo_ships_no_trading_period():
    """Undeterminable — the caller keeps its own fallback rather than guessing."""
    assert derive_market_state({}, now=XETRA_OPEN) is None


def test_returns_none_when_the_window_has_no_usable_bounds():
    assert derive_market_state({"currentTradingPeriod": {"regular": {}}}, now=1) is None


def test_explicit_market_state_from_yahoo_wins():
    """If Yahoo ever restores the field, it is authoritative."""
    meta = _meta(regular=(XETRA_OPEN, XETRA_CLOSE), marketState="POST")
    assert derive_market_state(meta, now=XETRA_OPEN + 3600) == "POST"
