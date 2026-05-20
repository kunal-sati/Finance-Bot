"""
Unit tests for bot.services.order_service.

Uses mocks to isolate the service layer from the exchange.
Tests cover validation delegation, precision adjustment,
dry-run mode, and error propagation.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from bot.core.exceptions import OrderError, PrecisionError, ValidationError
from bot.models.order_response import OrderResponse
from bot.services.order_service import OrderService


# ── Fixtures ─────────────────────────────────────────────────────────

MOCK_SYMBOL_INFO = {
    "symbol": "BTCUSDT",
    "quantityPrecision": 3,
    "pricePrecision": 2,
}

MOCK_EXCHANGE_RESPONSE = {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "orderId": 123456789,
    "status": "FILLED",
    "executedQty": "0.001",
    "avgPrice": "95000.00",
    "origQty": "0.001",
    "price": "0",
    "timeInForce": "GTC",
    "updateTime": 1700000000000,
}


@pytest.fixture
def mock_client() -> MagicMock:
    """Return a mocked BinanceFuturesClient."""
    client = MagicMock()
    client.get_symbol_info.return_value = MOCK_SYMBOL_INFO
    return client


@pytest.fixture
def service(mock_client: MagicMock) -> OrderService:
    """Return an OrderService wired to a mocked client."""
    svc = OrderService.__new__(OrderService)
    svc._client = mock_client
    from bot.exchange.futures import FuturesOperations
    svc._futures = FuturesOperations(mock_client)
    return svc


# ── Validation tests ────────────────────────────────────────────────


class TestOrderServiceValidation:
    """Tests that the service delegates validation correctly."""

    def test_invalid_side_raises(self, service: OrderService) -> None:
        with pytest.raises(ValidationError, match="Invalid order side"):
            service.create_order(
                symbol="BTCUSDT",
                side="HOLD",
                order_type="MARKET",
                quantity="0.001",
            )

    def test_invalid_order_type_raises(self, service: OrderService) -> None:
        with pytest.raises(ValidationError, match="Invalid order type"):
            service.create_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="STOP",
                quantity="0.001",
            )

    def test_invalid_quantity_raises(self, service: OrderService) -> None:
        with pytest.raises(ValidationError, match="Invalid quantity"):
            service.create_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity="abc",
            )

    def test_negative_quantity_raises(self, service: OrderService) -> None:
        with pytest.raises(ValidationError, match="must be positive"):
            service.create_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity="-1",
            )

    def test_limit_without_price_raises(self, service: OrderService) -> None:
        with pytest.raises(ValidationError, match="required for LIMIT"):
            service.create_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="LIMIT",
                quantity="0.001",
            )

    def test_invalid_symbol_raises(self, service: OrderService) -> None:
        with pytest.raises(ValidationError, match="Invalid symbol"):
            service.create_order(
                symbol="BTC-USDT",
                side="BUY",
                order_type="MARKET",
                quantity="0.001",
            )


# ── Dry run tests ───────────────────────────────────────────────────


class TestOrderServiceDryRun:
    """Tests for dry-run mode."""

    def test_dry_run_returns_summary(self, service: OrderService) -> None:
        result = service.create_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.001",
            dry_run=True,
        )
        assert isinstance(result, dict)
        assert result["mode"] == "DRY RUN"
        assert result["status"] == "NOT SUBMITTED"
        assert result["symbol"] == "BTCUSDT"
        assert result["side"] == "BUY"

    def test_dry_run_limit(self, service: OrderService) -> None:
        result = service.create_order(
            symbol="BTCUSDT",
            side="SELL",
            order_type="LIMIT",
            quantity="0.001",
            price="95000",
            dry_run=True,
        )
        assert isinstance(result, dict)
        assert result["order_type"] == "LIMIT"
        assert result["price"] == "95000.00"


# ── Precision tests ─────────────────────────────────────────────────


class TestOrderServicePrecision:
    """Tests for precision handling."""

    def test_symbol_not_found_raises(self, service: OrderService) -> None:
        service._client.get_symbol_info.return_value = None
        with pytest.raises(PrecisionError, match="not found"):
            service.create_order(
                symbol="FAKECOIN",
                side="BUY",
                order_type="MARKET",
                quantity="0.001",
            )

    def test_quantity_rounds_correctly(self, service: OrderService) -> None:
        """Quantity 0.00156 at precision 3 should become 0.001."""
        result = service.create_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.00156",
            dry_run=True,
        )
        assert result["quantity"] == "0.001"


# ── Response parsing ────────────────────────────────────────────────


class TestOrderResponseParsing:
    """Tests for parsing exchange responses."""

    def test_from_exchange(self) -> None:
        response = OrderResponse.from_exchange(MOCK_EXCHANGE_RESPONSE)
        assert response.symbol == "BTCUSDT"
        assert response.order_id == 123456789
        assert response.status == "FILLED"
        assert response.executed_qty == Decimal("0.001")
        assert response.avg_price == Decimal("95000.00")

    def test_from_exchange_missing_optional_fields(self) -> None:
        minimal = {
            "symbol": "ETHUSDT",
            "side": "SELL",
            "type": "MARKET",
            "orderId": 1,
            "status": "NEW",
        }
        response = OrderResponse.from_exchange(minimal)
        assert response.symbol == "ETHUSDT"
        assert response.order_id == 1
        assert response.executed_qty == Decimal("0")
