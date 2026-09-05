from decimal import Decimal
from pathlib import Path

import pytest

from starboy.cost import PRICING_VERSION, calculate_cost
from starboy.usage import Usage, parse_claude_code_usage, parse_codex_usage

FIXTURES = Path(__file__).parent / "fixtures"


def test_costs_claude_fixture_usage() -> None:
    lines = (FIXTURES / "claude_code_stream.jsonl").read_text().splitlines()
    usage, _ = parse_claude_code_usage(lines)

    cost, version = calculate_cost(usage, "claude-sonnet-5")

    # 4 * $2 + 42,419 * $0.20 + 9,249 * $4 + 119 * $10, all per MTok.
    assert cost == Decimal("0.0466778")
    assert version == "2026-09-06"


def test_costs_codex_fixture_usage() -> None:
    lines = (FIXTURES / "codex_stream.jsonl").read_text().splitlines()
    usage, _ = parse_codex_usage(lines)

    cost, version = calculate_cost(usage, "gpt-5.6-terra")

    # 6,090 * $2 + 56,320 * $0.20 + 281 * $12, all per MTok.
    assert cost == Decimal("0.026816")
    assert version == "2026-09-06"


def test_cache_reads_cost_less_than_uncached_input() -> None:
    uncached_cost, _ = calculate_cost(
        Usage(1_000_000, 0, 0, 0, 0, 0), "claude-sonnet-5"
    )
    cached_cost, _ = calculate_cost(
        Usage(0, 1_000_000, 0, 0, 0, 0), "claude-sonnet-5"
    )

    assert cached_cost == Decimal("0.2")
    assert uncached_cost == Decimal(2)
    assert cached_cost < uncached_cost


def test_cache_writes_price_differently_from_cache_reads() -> None:
    read_cost, _ = calculate_cost(
        Usage(0, 1_000_000, 0, 0, 0, 0), "claude-sonnet-5"
    )
    write_5m_cost, _ = calculate_cost(
        Usage(0, 0, 1_000_000, 0, 0, 0), "claude-sonnet-5"
    )
    write_1h_cost, _ = calculate_cost(
        Usage(0, 0, 0, 1_000_000, 0, 0), "claude-sonnet-5"
    )

    assert read_cost == Decimal("0.2")
    assert write_5m_cost == Decimal("2.5")
    assert write_1h_cost == Decimal(4)


def test_zero_usage_costs_zero() -> None:
    cost, version = calculate_cost(Usage(0, 0, 0, 0, 0, 0), "gpt-5.6-terra")

    assert cost == Decimal(0)
    assert version == PRICING_VERSION


def test_unknown_model_raises() -> None:
    with pytest.raises(ValueError, match="unknown model"):
        calculate_cost(Usage(0, 0, 0, 0, 0, 0), "not-a-model")


def test_returns_pricing_version() -> None:
    _, version = calculate_cost(Usage(0, 0, 0, 0, 0, 0), "claude-sonnet-5")

    assert version == "2026-09-06"
