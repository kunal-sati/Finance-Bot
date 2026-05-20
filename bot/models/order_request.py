"""
Order request model.

Immutable, validated representation of an order intent before it is
sent to the exchange. Pydantic enforces constraints at construction
time so downstream code can trust the data.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from bot.core.enums import OrderSide, OrderType, TimeInForce


class OrderRequest(BaseModel):
    """
    Validated order request payload.

    Attributes:
        symbol: Trading pair (e.g. ``BTCUSDT``).
        side: ``BUY`` or ``SELL``.
        order_type: ``MARKET`` or ``LIMIT``.
        quantity: Order quantity (must be > 0).
        price: Limit price (required when ``order_type`` is ``LIMIT``).
        time_in_force: TIF policy for limit orders (defaults to ``GTC``).
        dry_run: If ``True``, the order will not be sent to the exchange.
    """

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Trading pair symbol, e.g. BTCUSDT.",
    )
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(
        ...,
        gt=0,
        description="Order quantity — must be positive.",
    )
    price: Decimal | None = Field(
        default=None,
        gt=0,
        description="Limit price — required for LIMIT orders.",
    )
    time_in_force: TimeInForce | None = Field(
        default=None,
        description="Time-in-force policy (only for LIMIT orders).",
    )
    dry_run: bool = Field(
        default=False,
        description="Validate only — do not submit to exchange.",
    )

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_limit_price(self) -> "OrderRequest":
        """Ensure LIMIT orders carry a price."""
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("price is required for LIMIT orders")
        return self

    @model_validator(mode="after")
    def _normalize_symbol(self) -> "OrderRequest":
        """Upper-case the symbol for consistency."""
        if self.symbol != self.symbol.upper():
            object.__setattr__(self, "symbol", self.symbol.upper())
        return self
