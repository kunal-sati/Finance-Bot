"""
Utility helpers for precision handling and formatting.

Centralizes exchange-precision logic so that services and CLI
can share the same rounding behaviour.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal
from typing import Any

from bot.core.exceptions import PrecisionError
from bot.core.logger import get_logger

logger = get_logger("utils.helpers")


def extract_precision(symbol_info: dict[str, Any]) -> tuple[int, int]:
    """
    Extract quantity and price precision from exchange symbol info.

    Args:
        symbol_info: A single symbol entry from ``GET /fapi/v1/exchangeInfo``.

    Returns:
        A ``(quantity_precision, price_precision)`` tuple.

    Raises:
        PrecisionError: If the required fields are missing.
    """
    try:
        qty_precision: int = int(symbol_info["quantityPrecision"])
        price_precision: int = int(symbol_info["pricePrecision"])
        logger.debug(
            "Precision for %s — qty=%d, price=%d",
            symbol_info.get("symbol", "?"),
            qty_precision,
            price_precision,
        )
        return qty_precision, price_precision
    except (KeyError, TypeError, ValueError) as exc:
        raise PrecisionError(
            f"Failed to extract precision from exchange info: {exc}",
            details={"symbol_info_keys": list(symbol_info.keys())},
        ) from exc


def round_decimal(value: Decimal, precision: int) -> Decimal:
    """
    Round a ``Decimal`` down to the given number of decimal places.

    Uses ``ROUND_DOWN`` (truncation) to avoid exceeding exchange limits.

    Args:
        value: The value to round.
        precision: Number of decimal places.

    Returns:
        Truncated ``Decimal``.
    """
    if precision <= 0:
        return value.quantize(Decimal("1"), rounding=ROUND_DOWN)
    quantizer = Decimal(10) ** -precision
    return value.quantize(quantizer, rounding=ROUND_DOWN)


def round_quantity(quantity: Decimal, precision: int) -> Decimal:
    """Round quantity to exchange-specified precision."""
    return round_decimal(quantity, precision)


def round_price(price: Decimal, precision: int) -> Decimal:
    """Round price to exchange-specified precision."""
    return round_decimal(price, precision)


def format_timestamp(ts_ms: int | None) -> str:
    """Convert a millisecond Unix timestamp to ISO-8601 string."""
    if ts_ms is None:
        return "N/A"
    from datetime import datetime, timezone

    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
