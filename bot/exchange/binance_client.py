"""
Low-level Binance client wrapper.

Encapsulates the ``python-binance`` SDK behind a thin adapter so that
the rest of the application never imports the SDK directly. This makes
it trivial to swap exchange backends or mock in tests.
"""

from __future__ import annotations

import time
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bot.config.settings import Settings, get_settings
from bot.core.exceptions import (
    AuthenticationError,
    ExchangeAPIError,
    ExchangeConnectionError,
)
from bot.core.logger import get_logger

logger = get_logger("exchange.client")


class BinanceFuturesClient:
    """
    Authenticated wrapper around the Binance Futures Testnet SDK.

    Responsibilities:
      - Initialize and configure the SDK client
      - Point requests at the testnet endpoint
      - Provide retry-aware request methods
      - Translate SDK exceptions into domain exceptions
      - Log request/response metadata and latency
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: Client | None = None
        self._connect()

    # ── Connection ───────────────────────────────────────────────────

    def _connect(self) -> None:
        """Establish an authenticated connection to the Futures Testnet."""
        try:
            logger.info(
                "Connecting to Binance Futures Testnet — %s",
                self._settings.base_url,
            )
            # Do NOT pass testnet=True — that swaps the spot API URL to
            # testnet.binance.vision, which rejects Futures Testnet keys.
            # Instead, we set the futures URLs manually and flip the flag.
            self._client = Client(
                api_key=self._settings.binance_api_key,
                api_secret=self._settings.binance_api_secret,
                testnet=False,
            )
            # Point futures URLs at the testnet endpoint
            testnet_fapi = f"{self._settings.base_url}/fapi"
            self._client.FUTURES_URL = testnet_fapi
            self._client.FUTURES_TESTNET_URL = testnet_fapi
            self._client.FUTURES_DATA_TESTNET_URL = (
                f"{self._settings.base_url}/futures/data"
            )
            # Enable the testnet flag so _create_futures_api_uri uses
            # FUTURES_TESTNET_URL
            self._client.testnet = True
            logger.info("Binance Futures Testnet connection established")
        except Exception as exc:
            logger.exception("Failed to initialize Binance client")
            raise ExchangeConnectionError(
                f"Could not connect to Binance Futures Testnet: {exc}"
            ) from exc

    @property
    def client(self) -> Client:
        """Return the underlying SDK client (guaranteed non-None)."""
        if self._client is None:
            raise ExchangeConnectionError("Binance client is not initialized")
        return self._client

    # ── Retry-aware request executor ─────────────────────────────────

    def execute(
        self,
        method_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a named SDK method with retries, logging, and error translation.

        Args:
            method_name: Attribute name on the SDK ``Client`` (e.g.
                ``futures_create_order``).
            **kwargs: Keyword arguments forwarded to the SDK method.

        Returns:
            The parsed JSON response from Binance.

        Raises:
            ExchangeAPIError: On non-retryable API errors.
            ExchangeConnectionError: On network / connection errors.
            AuthenticationError: On 401/403 responses.
        """
        return self._execute_with_retry(method_name, **kwargs)

    @retry(
        retry=retry_if_exception_type(ExchangeConnectionError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def _execute_with_retry(
        self,
        method_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Inner retry loop — only retries connection-level failures."""
        method = getattr(self.client, method_name, None)
        if method is None:
            raise ExchangeAPIError(
                f"Unknown SDK method: {method_name}",
                details={"method": method_name},
            )

        logger.info(
            "API request  → %s | params=%s",
            method_name,
            {k: v for k, v in kwargs.items() if k != "api_secret"},
        )
        start = time.perf_counter()

        try:
            response = method(**kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "API response ← %s | latency=%.1f ms | response=%s",
                method_name,
                elapsed_ms,
                response,
            )
            return response  # type: ignore[return-value]

        except BinanceAPIException as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "Binance API error — %s | code=%s | latency=%.1f ms",
                exc.message,
                exc.code,
                elapsed_ms,
            )
            if exc.code in (-2014, -2015):
                raise AuthenticationError(
                    f"Authentication failed: {exc.message}",
                    details={"code": exc.code},
                ) from exc
            raise ExchangeAPIError(
                message=exc.message,
                status_code=exc.code,
                details={"code": exc.code, "method": method_name},
            ) from exc

        except BinanceRequestException as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.warning(
                "Network/request error — %s | latency=%.1f ms — will retry",
                exc,
                elapsed_ms,
            )
            raise ExchangeConnectionError(
                f"Request failed: {exc}"
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected error during API call: %s", method_name)
            raise ExchangeConnectionError(
                f"Unexpected error: {exc}"
            ) from exc

    # ── Convenience accessors ────────────────────────────────────────

    def get_exchange_info(self) -> dict[str, Any]:
        """Fetch Futures exchange info (symbols, precision, filters)."""
        return self.execute("futures_exchange_info")

    def get_symbol_info(self, symbol: str) -> dict[str, Any] | None:
        """
        Return the exchange-info entry for a single symbol.

        Returns ``None`` if the symbol is not listed.
        """
        info = self.get_exchange_info()
        for s in info.get("symbols", []):
            if s["symbol"] == symbol.upper():
                return s  # type: ignore[return-value]
        return None
