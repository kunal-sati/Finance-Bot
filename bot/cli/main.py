"""
CLI entry point for the trading bot.

Uses **Typer** for argument parsing and **Rich** for terminal output.
Invocable via:

    python -m bot.cli.main --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
"""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bot.core.enums import OrderSide, OrderType
from bot.core.exceptions import TradingBotError
from bot.core.logger import get_logger, setup_logging
from bot.models.order_response import OrderResponse
from bot.services.order_service import OrderService

logger = get_logger("cli")
console = Console()

app = typer.Typer(
    name="trading-bot",
    help="🚀 Binance Futures Testnet Trading Bot",
    add_completion=False,
    rich_markup_mode="rich",
)


def _render_order_response(response: OrderResponse) -> None:
    """Display a successful order response as a Rich table."""
    table = Table(
        title="✅  Order Executed",
        box=box.ROUNDED,
        title_style="bold green",
        border_style="green",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Field", style="bold white", min_width=16)
    table.add_column("Value", style="bright_white")

    table.add_row("Symbol", response.symbol)
    table.add_row("Side", response.side)
    table.add_row("Type", response.order_type)
    table.add_row("Order ID", str(response.order_id))
    table.add_row("Status", response.status)
    table.add_row("Original Qty", str(response.orig_qty))
    table.add_row("Executed Qty", str(response.executed_qty))
    table.add_row("Avg Price", str(response.avg_price))
    table.add_row("Price", str(response.price))
    table.add_row("Time In Force", response.time_in_force)
    table.add_row(
        "Timestamp",
        response.transact_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        if response.transact_time
        else "N/A",
    )

    console.print()
    console.print(table)
    console.print()


def _render_dry_run(summary: dict) -> None:
    """Display dry-run summary as a Rich panel."""
    table = Table(
        box=box.SIMPLE_HEAVY,
        show_header=False,
        border_style="yellow",
    )
    table.add_column("Field", style="bold yellow")
    table.add_column("Value", style="white")

    for key, value in summary.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    panel = Panel(
        table,
        title="🔍  Dry Run — Order Preview",
        title_align="left",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)
    console.print()


def _render_error(message: str) -> None:
    """Display an error message as a Rich panel."""
    console.print()
    console.print(
        Panel(
            f"[bold red]{message}[/bold red]",
            title="❌  Error",
            title_align="left",
            border_style="red",
            padding=(1, 2),
        )
    )
    console.print()


@app.command()
def place_order(
    symbol: str = typer.Option(
        ...,
        "--symbol",
        "-s",
        help="Trading pair symbol (e.g. BTCUSDT).",
    ),
    side: str = typer.Option(
        ...,
        "--side",
        help="Order side: BUY or SELL.",
    ),
    order_type: str = typer.Option(
        ...,
        "--type",
        "-t",
        help="Order type: MARKET or LIMIT.",
    ),
    quantity: float = typer.Option(
        ...,
        "--quantity",
        "-q",
        help="Order quantity (must be positive).",
    ),
    price: Optional[float] = typer.Option(
        None,
        "--price",
        "-p",
        help="Limit price (required for LIMIT orders).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate and preview order without submitting.",
    ),
) -> None:
    """
    Place an order on Binance Futures Testnet.

    Supports MARKET and LIMIT orders for both BUY and SELL sides.
    Use --dry-run to validate without submitting.
    """
    setup_logging()

    console.print(
        Panel(
            "[bold bright_white]Binance Futures Testnet Trading Bot[/bold bright_white]",
            border_style="bright_cyan",
            padding=(0, 2),
        )
    )

    try:
        service = OrderService()
        result = service.create_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            dry_run=dry_run,
        )

        if isinstance(result, OrderResponse):
            _render_order_response(result)
        else:
            _render_dry_run(result)

    except TradingBotError as exc:
        logger.error("Trading bot error: %s", exc.message)
        _render_error(exc.message)
        raise typer.Exit(code=1)

    except Exception as exc:
        logger.exception("Unexpected error")
        _render_error(f"Unexpected error: {exc}")
        raise typer.Exit(code=1)


# Allow `python -m bot.cli.main`
if __name__ == "__main__":
    app()
