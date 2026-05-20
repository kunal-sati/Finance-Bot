"""
High-level Futures order operations.

Translates domain models into SDK-compatible parameters and delegates
execution to the :class:`BinanceFuturesClient`.
"""

from __future__ import annotations

from typing import Any

from bot.core.enums import OrderType, TimeInForce
from bot.core.logger import get_logger
from bot.exchange.binance_client import BinanceFuturesClient
from bot.models.order_request import OrderRequest

logger = get_logger("exchange.futures")


class FuturesOperations:
    """
    Provides domain-oriented order operations on top of the raw client.

    This layer is responsible for:
      - Building SDK parameter dicts from validated ``OrderRequest`` models
      - Delegating to the retry-aware client
      - Returning raw exchange response dicts
    """

    def __init__(self, client: BinanceFuturesClient) -> None:
        self._client = client

    def place_order(self, request: OrderRequest) -> dict[str, Any]:
        """
        Place a Futures order.

        Args:
            request: A fully validated and precision-adjusted order request.

        Returns:
            Raw response dict from the exchange.
        """
        params = self._build_order_params(request)
        logger.info("Placing futures order — %s", params)
        return self._client.execute("futures_create_order", **params)

    @staticmethod
    def _build_order_params(request: OrderRequest) -> dict[str, Any]:
        """Convert an ``OrderRequest`` into SDK keyword arguments."""
        params: dict[str, Any] = {
            "symbol": request.symbol,
            "side": request.side.value,
            "type": request.order_type.value,
            "quantity": str(request.quantity),
        }
        if request.order_type == OrderType.LIMIT:
            assert request.price is not None, "Limit orders must have a price"
            params["price"] = str(request.price)
            params["timeInForce"] = (
                request.time_in_force or TimeInForce.GTC
            ).value

        return params
