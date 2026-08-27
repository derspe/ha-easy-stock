"""Unit tests for the position arithmetic behind the purchase-price attributes."""
from custom_components.easy_stock.portfolio import position_attributes


def test_no_purchase_price_yields_no_attributes():
    """Sensors without a configured position must look exactly as before."""
    assert position_attributes(195.0, None) == {}
    assert position_attributes(195.0, 0) == {}
    assert position_attributes(195.0, "") == {}


def test_negative_purchase_price_is_ignored():
    assert position_attributes(195.0, -10) == {}


def test_per_unit_figures_without_quantity():
    """A price alone is enough for gain per unit and percent."""
    attrs = position_attributes(195.0, 150.0)
    assert attrs["purchase_price"] == 150.0
    assert attrs["gain_per_unit"] == 45.0
    assert attrs["gain_pct"] == 30.0


def test_quantity_zero_is_treated_as_not_entered():
    """0 is the form's "unset" value -- it must not produce a 0 EUR position."""
    attrs = position_attributes(195.0, 150.0, 0)
    assert "quantity" not in attrs
    assert "position_value" not in attrs
    assert "invested" not in attrs
    assert "gain_total" not in attrs


def test_quantity_adds_lot_figures():
    attrs = position_attributes(195.0, 150.0, 10)
    assert attrs["quantity"] == 10
    assert attrs["invested"] == 1500.0
    assert attrs["position_value"] == 1950.0
    assert attrs["gain_total"] == 450.0


def test_loss_is_reported_as_negative():
    attrs = position_attributes(120.0, 150.0, 4)
    assert attrs["gain_per_unit"] == -30.0
    assert attrs["gain_total"] == -120.0
    assert attrs["gain_pct"] == -20.0


def test_fractional_quantity_and_small_prices():
    """Crypto positions are fractions of a unit and must not round to nothing."""
    attrs = position_attributes(67840.33, 0.0512, 0.25)
    assert attrs["purchase_price"] == 0.0512
    assert attrs["quantity"] == 0.25
    assert attrs["position_value"] == 16960.08


def test_missing_current_price_keeps_the_static_figures():
    """A failed poll must not wipe the numbers the user typed in."""
    attrs = position_attributes(None, 150.0, 10)
    assert attrs == {"purchase_price": 150.0, "quantity": 10, "invested": 1500.0}


def test_strings_from_the_config_entry_are_accepted():
    """Values that came back from storage as strings still have to compute."""
    attrs = position_attributes("195.0", "150.0", "10")
    assert attrs["gain_total"] == 450.0
