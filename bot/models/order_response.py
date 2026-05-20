"""
Order response model.

Normalizes the raw exchange response into a typed, predictable structure
that the CLI and other consumers can rely on without parsing dicts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class OrderResponse(BaseModel):
    """
    Parsed order response from the exchange.

    Fields mirror the most useful subset of the Binance Futures
    ``POST /fapi/v1/order`` response.
    """

    symbol: str
    side: str
    order_type: str = Field(alias="type")
    order_id: int = Field(alias="orderId")
    status: str
    executed_qty: Decimal = Field(alias="executedQty", default=Decimal("0"))
    avg_price: Decimal = Field(alias="avgPrice", default=Decimal("0"))
    orig_qty: Decimal = Field(alias="origQty", default=Decimal("0"))
    price: Decimal = Field(default=Decimal("0"))
    time_in_force: str = Field(alias="timeInForce", default="GTC")
    transact_time: datetime | None = Field(alias="updateTime", default=None)

    model_config = {"populate_by_name": True}

    @field_validator("transact_time", mode="before")
    @classmethod
    def _parse_timestamp(cls, v: int | datetime | None) -> datetime | None:
        if isinstance(v, int):
            return datetime.fromtimestamp(v / 1000, tz=timezone.utc)
        return v

    @classmethod
    def from_exchange(cls, data: dict) -> "OrderResponse":
        """
        Factory that gracefully handles missing or unexpected fields.

        Args:
            data: Raw JSON dict from the exchange.

        Returns:
            A validated ``OrderResponse``.
        """
        return cls.model_validate(data)
