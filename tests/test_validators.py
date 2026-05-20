"""
Unit tests for bot.utils.validators.

Covers happy-path and error-path scenarios for every public validator
function, ensuring that validation messages are clear and that edge
cases (empty strings, negative numbers, wrong types) are handled.
"""

from decimal import Decimal

import pytest

from bot.core.enums import OrderSide, OrderType
from bot.core.exceptions import ValidationError
from bot.utils.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)


# ── validate_symbol ─────────────────────────────────────────────────


class TestValidateSymbol:
    """Tests for symbol validation."""

    def test_valid_symbol(self) -> None:
        assert validate_symbol("BTCUSDT") == "BTCUSDT"

    def test_lowercase_normalized(self) -> None:
        assert validate_symbol("btcusdt") == "BTCUSDT"

    def test_mixed_case(self) -> None:
        assert validate_symbol("BtcUsdt") == "BTCUSDT"

    def test_with_whitespace(self) -> None:
        assert validate_symbol("  ETHUSDT  ") == "ETHUSDT"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="must not be empty"):
            validate_symbol("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValidationError, match="must not be empty"):
            validate_symbol("   ")

    def test_special_characters_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid symbol format"):
            validate_symbol("BTC-USDT")

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid symbol format"):
            validate_symbol("A" * 21)

    def test_single_char_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid symbol format"):
            validate_symbol("B")


# ── validate_side ────────────────────────────────────────────────────


class TestValidateSide:
    """Tests for order side validation."""

    def test_buy(self) -> None:
        assert validate_side("BUY") == OrderSide.BUY

    def test_sell(self) -> None:
        assert validate_side("SELL") == OrderSide.SELL

    def test_lowercase(self) -> None:
        assert validate_side("buy") == OrderSide.BUY

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid order side"):
            validate_side("HOLD")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid order side"):
            validate_side("")


# ── validate_order_type ──────────────────────────────────────────────


class TestValidateOrderType:
    """Tests for order type validation."""

    def test_market(self) -> None:
        assert validate_order_type("MARKET") == OrderType.MARKET

    def test_limit(self) -> None:
        assert validate_order_type("LIMIT") == OrderType.LIMIT

    def test_lowercase(self) -> None:
        assert validate_order_type("market") == OrderType.MARKET

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid order type"):
            validate_order_type("STOP_LOSS")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid order type"):
            validate_order_type("")


# ── validate_quantity ────────────────────────────────────────────────


class TestValidateQuantity:
    """Tests for quantity validation."""

    def test_valid_decimal_string(self) -> None:
        assert validate_quantity("0.001") == Decimal("0.001")

    def test_valid_float(self) -> None:
        assert validate_quantity(1.5) == Decimal("1.5")

    def test_valid_int_as_string(self) -> None:
        assert validate_quantity("10") == Decimal("10")

    def test_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be positive"):
            validate_quantity("0")

    def test_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be positive"):
            validate_quantity("-1")

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid quantity"):
            validate_quantity("abc")


# ── validate_price ───────────────────────────────────────────────────


class TestValidatePrice:
    """Tests for price validation."""

    def test_limit_with_valid_price(self) -> None:
        result = validate_price("95000.50", OrderType.LIMIT)
        assert result == Decimal("95000.50")

    def test_limit_without_price_raises(self) -> None:
        with pytest.raises(ValidationError, match="required for LIMIT"):
            validate_price(None, OrderType.LIMIT)

    def test_limit_negative_price_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be positive"):
            validate_price("-100", OrderType.LIMIT)

    def test_limit_zero_price_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be positive"):
            validate_price("0", OrderType.LIMIT)

    def test_market_ignores_price(self) -> None:
        assert validate_price("99999", OrderType.MARKET) is None

    def test_market_none_price(self) -> None:
        assert validate_price(None, OrderType.MARKET) is None

    def test_non_numeric_price_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid price"):
            validate_price("abc", OrderType.LIMIT)
