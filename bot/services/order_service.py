"""
Order service — the central orchestrator for placing orders.

Owns the full lifecycle:
  1. Validate inputs
  2. Fetch exchange precision
  3. Round quantity / price
  4. Delegate to the exchange layer
  5. Parse and return a typed response
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from bot.core.enums import OrderType
from bot.core.exceptions import OrderError, PrecisionError, ValidationError
from bot.core.logger import get_logger
from bot.exchange.binance_client import BinanceFuturesClient
from bot.exchange.futures import FuturesOperations
from bot.models.order_request import OrderRequest
from bot.models.order_response import OrderResponse
from bot.utils.helpers import extract_precision, round_price, round_quantity
from bot.utils.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)

logger = get_logger("services.order")


class OrderService:
    """
    Application service for creating and submitting Futures orders.

    Depends on:
      - :class:`BinanceFuturesClient` for exchange connectivity
      - :class:`FuturesOperations` for SDK-level order placement
    """

    def __init__(self, client: BinanceFuturesClient | None = None) -> None:
        self._client = client or BinanceFuturesClient()
        self._futures = FuturesOperations(self._client)

    # ── Public API ───────────────────────────────────────────────────

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str | float | Decimal,
        price: str | float | Decimal | None = None,
        dry_run: bool = False,
    ) -> OrderResponse | dict[str, Any]:
        """
        Validate, adjust precision, and place a Futures order.

        Args:
            symbol: Trading pair (e.g. ``BTCUSDT``).
            side: ``BUY`` or ``SELL``.
            order_type: ``MARKET`` or ``LIMIT``.
            quantity: Order quantity.
            price: Limit price (required for LIMIT).
            dry_run: If ``True``, validate and log but do NOT submit.

        Returns:
            :class:`OrderResponse` on success, or a summary dict in dry-run mode.

        Raises:
            ValidationError: On invalid inputs.
            PrecisionError: If exchange info cannot be fetched.
            OrderError: On placement failure after validation passes.
        """
        # ── Step 1: Validate raw inputs ──────────────────────────────
        validated_symbol = validate_symbol(symbol)
        validated_side = validate_side(side)
        validated_type = validate_order_type(order_type)
        validated_qty = validate_quantity(quantity)
        validated_price = validate_price(price, validated_type)

        logger.info(
            "Order intent — symbol=%s side=%s type=%s qty=%s price=%s dry_run=%s",
            validated_symbol,
            validated_side,
            validated_type,
            validated_qty,
            validated_price,
            dry_run,
        )

        # ── Step 2: Fetch precision ──────────────────────────────────
        qty_precision, price_precision = self._fetch_precision(validated_symbol)

        # ── Step 3: Round ────────────────────────────────────────────
        adjusted_qty = round_quantity(validated_qty, qty_precision)
        adjusted_price = (
            round_price(validated_price, price_precision)
            if validated_price is not None
            else None
        )

        if adjusted_qty <= 0:
            raise ValidationError(
                f"Quantity {validated_qty} rounds to zero at precision {qty_precision}. "
                "Increase the quantity."
            )

        logger.info(
            "Precision-adjusted — qty=%s (precision=%d) price=%s (precision=%d)",
            adjusted_qty,
            qty_precision,
            adjusted_price,
            price_precision,
        )

        # ── Step 4: Build request model ──────────────────────────────
        request = OrderRequest(
            symbol=validated_symbol,
            side=validated_side,
            order_type=validated_type,
            quantity=adjusted_qty,
            price=adjusted_price,
            dry_run=dry_run,
        )

        # ── Step 5: Dry run or live ──────────────────────────────────
        if dry_run:
            return self._dry_run_summary(request)

        return self._submit_order(request)

    # ── Internal helpers ─────────────────────────────────────────────

    def _fetch_precision(self, symbol: str) -> tuple[int, int]:
        """Retrieve and extract precision for the given symbol."""
        symbol_info = self._client.get_symbol_info(symbol)
        if symbol_info is None:
            raise PrecisionError(
                f"Symbol '{symbol}' not found on the exchange. "
                "Verify the symbol or check Futures Testnet availability."
            )
        return extract_precision(symbol_info)

    def _submit_order(self, request: OrderRequest) -> OrderResponse:
        """Place the order and parse the response."""
        try:
            raw = self._futures.place_order(request)
            response = OrderResponse.from_exchange(raw)
            logger.info("Order placed successfully — orderId=%s", response.order_id)
            return response
        except Exception as exc:
            logger.exception("Order placement failed")
            if isinstance(exc, (ValidationError, PrecisionError)):
                raise
            raise OrderError(
                f"Failed to place order: {exc}",
                details={"symbol": request.symbol, "side": request.side.value},
            ) from exc

    @staticmethod
    def _dry_run_summary(request: OrderRequest) -> dict[str, Any]:
        """Return a human-readable summary without hitting the exchange."""
        summary = {
            "mode": "DRY RUN",
            "symbol": request.symbol,
            "side": request.side.value,
            "order_type": request.order_type.value,
            "quantity": str(request.quantity),
            "price": str(request.price) if request.price else "MARKET",
            "status": "NOT SUBMITTED",
        }
        logger.info("Dry-run summary — %s", summary)
        return summary
