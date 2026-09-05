from pathlib import Path

import pytest

from starboy.usage import Usage, parse_claude_code_usage, parse_codex_usage

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def claude_lines() -> list[str]:
    return (FIXTURES / "claude_code_stream.jsonl").read_text().splitlines()


@pytest.fixture
def codex_lines() -> list[str]:
    return (FIXTURES / "codex_stream.jsonl").read_text().splitlines()


def test_parses_claude_code_fixture(claude_lines: list[str]) -> None:
    usage, session_id = parse_claude_code_usage(claude_lines)

    # This capture reused a warm Claude prompt cache from a recent CLI run.
    # Its 4 uncached tokens and 42,419 cache reads are therefore not representative
    # of a fresh agent run, but are intentional fixture values rather than a parsing bug.
    assert usage == Usage(
        uncached_input_tokens=4,
        cache_read_tokens=42419,
        cache_write_tokens=9249,
        output_tokens=119,
        reasoning_tokens=0,
    )
    assert session_id == "2c2c58f3-d008-4b6c-ab0c-7420bce801f9"
    assert usage.uncached_input_tokens >= 0


def test_parses_codex_fixture(codex_lines: list[str]) -> None:
    usage, session_id = parse_codex_usage(codex_lines)

    assert usage == Usage(
        uncached_input_tokens=6090,
        cache_read_tokens=56320,
        cache_write_tokens=0,
        output_tokens=281,
        reasoning_tokens=9,
    )
    assert usage.uncached_input_tokens + usage.cache_read_tokens == 62410
    assert usage.uncached_input_tokens >= 0
    assert session_id == "01a0712e-5dcf-7f60-a4b9-8a9eaa1d20ef"


def test_parses_final_turn_of_codex_two_turn_fixture() -> None:
    lines = (FIXTURES / "codex_two_turn_stream.jsonl").read_text().splitlines()

    usage, session_id = parse_codex_usage(lines)

    assert usage == Usage(
        uncached_input_tokens=1741,
        cache_read_tokens=14080,
        cache_write_tokens=0,
        output_tokens=6,
        reasoning_tokens=0,
    )
    assert session_id == "01a073d6-e5c2-7a12-8335-a27fb60c1161"


@pytest.mark.parametrize(
    ("parser", "fixture_name"),
    [
        (parse_claude_code_usage, "claude_code_stream.jsonl"),
        (parse_codex_usage, "codex_stream.jsonl"),
    ],
)
def test_truncated_stream_returns_zero_usage(
    parser: object, fixture_name: str
) -> None:
    lines = (FIXTURES / fixture_name).read_text().splitlines()[:-1]
    usage, _ = parser(lines)  # type: ignore[operator]

    assert usage == Usage(0, 0, 0, 0, 0)


@pytest.mark.parametrize(
    ("parser", "fixture_name", "expected"),
    [
        (
            parse_claude_code_usage,
            "claude_code_stream.jsonl",
            Usage(4, 42419, 9249, 119, 0),
        ),
        (
            parse_codex_usage,
            "codex_stream.jsonl",
            Usage(6090, 56320, 0, 281, 9),
        ),
    ],
)
def test_skips_malformed_lines(
    parser: object, fixture_name: str, expected: Usage
) -> None:
    lines = (FIXTURES / fixture_name).read_text().splitlines()
    lines.insert(1, "this is not JSON")

    usage, _ = parser(lines)  # type: ignore[operator]

    assert usage == expected
