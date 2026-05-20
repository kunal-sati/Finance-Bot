"""
Enumeration types for the trading bot.

Defines strongly-typed enums for order sides, order types,
and other domain constants used throughout the application.
"""

from enum import Enum


class OrderSide(str, Enum):
    """Trading order side — direction of the trade."""

    BUY = "BUY"
    SELL = "SELL"

    def __str__(self) -> str:
        return self.value


class OrderType(str, Enum):
    """Trading order type — execution strategy."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"

    def __str__(self) -> str:
        return self.value


class TimeInForce(str, Enum):
    """Time-in-force policy for limit orders."""

    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill

    def __str__(self) -> str:
        return self.value
