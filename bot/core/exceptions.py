"""
Custom exception hierarchy for the trading bot.

Provides granular, domain-specific exceptions that allow callers
to handle different failure modes (validation, exchange, network)
without coupling to third-party SDK exception types.
"""


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(TradingBotError):
    """Raised when order input validation fails."""

    pass


class ExchangeConnectionError(TradingBotError):
    """Raised when connection to the exchange cannot be established."""

    pass


class ExchangeAPIError(TradingBotError):
    """Raised when the exchange API returns an error response."""

    def __init__(
        self, message: str, status_code: int | None = None, details: dict | None = None
    ) -> None:
        self.status_code = status_code
        super().__init__(message, details)


class AuthenticationError(TradingBotError):
    """Raised when API key or secret is invalid or missing."""

    pass


class OrderError(TradingBotError):
    """Raised when order placement fails after passing validation."""

    pass


class PrecisionError(TradingBotError):
    """Raised when exchange precision info cannot be retrieved or applied."""

    pass


class ConfigurationError(TradingBotError):
    """Raised when application configuration is invalid or incomplete."""

    pass
