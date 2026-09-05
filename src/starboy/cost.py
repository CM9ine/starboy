"""Calculate API-equivalent token costs from normalised usage."""

from __future__ import annotations

from decimal import Decimal

from starboy.usage import Usage

PRICING_VERSION = "2026-09-06"

# Dollar rates per million tokens, captured on PRICING_VERSION.
_PRICES_PER_MTOK = {
    "claude-sonnet-5": (
        Decimal(2),
        Decimal("0.2"),
        Decimal("2.5"),
        Decimal(4),
        Decimal(10),
    ),
    "gpt-5.6-terra": (
        Decimal(2),
        Decimal("0.2"),
        Decimal("2.5"),
        Decimal("2.5"),
        Decimal(12),
    ),
}


def calculate_cost(usage: Usage, model: str) -> tuple[Decimal, str]:
    """Return API-equivalent dollar cost and the pricing-table version."""

    try:
        (
            uncached_input_rate,
            cache_read_rate,
            cache_write_5m_rate,
            cache_write_1h_rate,
            output_rate,
        ) = _PRICES_PER_MTOK[model]
    except KeyError as error:
        raise ValueError(f"unknown model: {model}") from error

    cost = (
        usage.uncached_input_tokens * uncached_input_rate
        + usage.cache_read_tokens * cache_read_rate
        + usage.cache_write_5m_tokens * cache_write_5m_rate
        + usage.cache_write_1h_tokens * cache_write_1h_rate
        + usage.output_tokens * output_rate
    ) / Decimal(1_000_000)
    return cost, PRICING_VERSION
