import pytest

from benchmarks import BENCHMARKS
from custom_cases import MAX_CUSTOM_CASES, parse_custom_cases
from harness import TestCase, evaluate, validate_candidate, values_equal


@pytest.mark.parametrize("problem", BENCHMARKS, ids=lambda p: p.id)
def test_reference_solutions_pass_their_benchmark(problem):
    result = evaluate(problem.reference_solution, problem.tests, timeout=3)
    assert result.passed == result.total, (problem.id, [c for c in result.cases if not c.passed])


def test_scores_correctness_and_edge_cases():
    result = evaluate("def solve(data): return data['x']", [TestCase("normal", {"x": 1}, 1), TestCase("edge", {"x": 0}, 1, True)])
    assert result.status == "complete"
    assert result.score == .5
    assert (result.edge_passed, result.edge_total) == (0, 1)


def test_rejects_syntax_and_disallowed_imports():
    assert "Syntax error" in validate_candidate("def solve(:")
    assert "blocked" in validate_candidate("import socket\ndef solve(data): return 1")


def test_timeout_is_reported():
    result = evaluate("def solve(data):\n    while True: pass", [TestCase("hang", {}, 1)], timeout=.2)
    assert result.passed == 0
    assert "Timed out" in result.cases[0].error


def test_nested_numeric_comparison_uses_tolerance():
    assert values_equal({"x": [1.00000001]}, {"x": [1.0]})
    assert not values_equal(True, 1)


@pytest.mark.parametrize("raw, message", [
    ("{}", "JSON array"),
    ("[]", "at least one"),
    ("[1]", "must be a JSON object"),
    ('[{"name":"missing input","expected":1}]', "missing required field"),
    ('[{"input":{},"expected":1,"edge_case":"no"}]', "must be true or false"),
    ('[{"name":"  ","input":{},"expected":1}]', "non-empty string"),
])
def test_custom_case_parser_rejects_malformed_shapes(raw, message):
    with pytest.raises(ValueError, match=message):
        parse_custom_cases(raw)


def test_custom_case_parser_accepts_valid_cases_and_defaults():
    cases = parse_custom_cases('[{"name":" edge ","input":{"x":0},"expected":0,"edge_case":true},{"input":{},"expected":1}]')
    assert cases == [TestCase("edge", {"x": 0}, 0, True), TestCase("case 2", {}, 1, False)]


def test_custom_case_parser_limits_count_and_payload_size():
    with pytest.raises(ValueError, match="no more than"):
        parse_custom_cases("[" + ",".join('{"input":{},"expected":0}' for _ in range(MAX_CUSTOM_CASES + 1)) + "]")
    with pytest.raises(ValueError, match="characters or fewer"):
        parse_custom_cases(" " * 100_001)
