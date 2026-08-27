"""Turn a purchase price and a lot size into position figures.

Yahoo only knows what an asset costs right now. The number a holder
actually looks for -- am I up or down on this position -- needs two values
the feed can never supply: the price that was paid and how many units were
bought. Both are static per config entry, so they are stored with the entry
and folded into the sensor's attributes from here.

Deliberately free of Home Assistant imports, like ``market_state``: the
arithmetic is the part worth testing, and it should not need a hass fixture
to do so.
"""

MONEY_PRECISION = 2
# Purchase prices are entered per unit and can be small enough that two
# decimals would swallow the value entirely -- a fraction of a Bitcoin, a
# penny stock. Four keeps the input recognizable when it is echoed back.
UNIT_PRECISION = 4


def _as_number(value) -> float | None:
    """Return ``value`` as a float, or None if it is not usable as one."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def position_attributes(
    current_price, purchase_price, quantity=None
) -> dict[str, float]:
    """Return the position attributes for one holding.

    ``purchase_price`` is what was paid per unit, in the currency the sensor
    reports. A missing or non-positive value means no position is configured:
    the result is empty and the sensor keeps exactly the attributes it had
    before this feature existed, rather than growing a row of zeros.

    ``quantity`` is optional on its own. Without it only the per-unit figures
    are meaningful, so the lot-size attributes are left out instead of being
    reported as zero -- a quantity of 0 and "quantity not entered" would
    otherwise be indistinguishable in the card and in templates.
    """
    purchase = _as_number(purchase_price)
    if purchase is None or purchase <= 0:
        return {}

    price = _as_number(current_price)
    units = _as_number(quantity)
    if units is not None and units <= 0:
        units = None

    attrs: dict[str, float] = {"purchase_price": round(purchase, UNIT_PRECISION)}

    if units is not None:
        attrs["quantity"] = round(units, UNIT_PRECISION)
        attrs["invested"] = round(purchase * units, MONEY_PRECISION)

    if price is None:
        return attrs

    if units is not None:
        attrs["position_value"] = round(price * units, MONEY_PRECISION)
        attrs["gain_total"] = round(price * units - purchase * units, MONEY_PRECISION)

    attrs["gain_per_unit"] = round(price - purchase, UNIT_PRECISION)
    attrs["gain_pct"] = round((price - purchase) / purchase * 100, MONEY_PRECISION)
    return attrs
