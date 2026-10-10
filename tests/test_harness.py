import pytest

from benchmarks import BENCHMARKS
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
