"""
Input validators for order parameters.

All validators raise :class:`bot.core.exceptions.ValidationError` with
descriptive messages so callers can surface them directly to the user.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from bot.core.enums import OrderSide, OrderType
from bot.core.exceptions import ValidationError


_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,20}$")


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize a trading pair symbol.

    Rules:
      - Must be 2-20 uppercase alphanumeric characters.
      - Automatically upper-cased.

    Returns:
        The normalized (upper-case) symbol.

    Raises:
        ValidationError: If the symbol is empty or malformed.
    """
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol must not be empty")

    normalized = symbol.strip().upper()
    if not _SYMBOL_PATTERN.match(normalized):
        raise ValidationError(
            f"Invalid symbol format: '{symbol}'. "
            "Expected 2-20 uppercase alphanumeric characters (e.g. BTCUSDT)."
        )
    return normalized


def validate_side(side: str) -> OrderSide:
    """
    Validate and convert an order side string to :class:`OrderSide`.

    Raises:
        ValidationError: If side is not ``BUY`` or ``SELL``.
    """
    try:
        return OrderSide(side.strip().upper())
    except (ValueError, AttributeError):
        raise ValidationError(
            f"Invalid order side: '{side}'. Must be BUY or SELL."
        )


def validate_order_type(order_type: str) -> OrderType:
    """
    Validate and convert an order type string to :class:`OrderType`.

    Raises:
        ValidationError: If type is not ``MARKET`` or ``LIMIT``.
    """
    try:
        return OrderType(order_type.strip().upper())
    except (ValueError, AttributeError):
        raise ValidationError(
            f"Invalid order type: '{order_type}'. Must be MARKET or LIMIT."
        )


def validate_quantity(quantity: str | float | Decimal) -> Decimal:
    """
    Validate that quantity is a positive number.

    Raises:
        ValidationError: If quantity is non-numeric, zero, or negative.
    """
    try:
        qty = Decimal(str(quantity))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            f"Invalid quantity: '{quantity}'. Must be a positive number."
        )

    if qty <= 0:
        raise ValidationError(
            f"Quantity must be positive, got {qty}."
        )
    return qty


def validate_price(
    price: str | float | Decimal | None,
    order_type: OrderType,
) -> Decimal | None:
    """
    Validate limit price.

    - Required for LIMIT orders.
    - Must be positive if supplied.
    - Ignored for MARKET orders (returns ``None``).

    Raises:
        ValidationError: On missing / invalid price for LIMIT orders.
    """
    if order_type == OrderType.MARKET:
        return None

    if price is None:
        raise ValidationError("Price is required for LIMIT orders.")

    try:
        p = Decimal(str(price))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            f"Invalid price: '{price}'. Must be a positive number."
        )

    if p <= 0:
        raise ValidationError(f"Price must be positive, got {p}.")
    return p
