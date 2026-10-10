"""Dependency-free smoke check for benchmark and core evaluation behavior."""
from __future__ import annotations

import argparse
import json
import sys

from benchmarks import BENCHMARKS
from harness import TestCase, compare, evaluate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=3.0, help="timeout per test case in seconds")
    args = parser.parse_args()
    failures = []
    total = 0
    for problem in BENCHMARKS:
        result = evaluate(problem.reference_solution, problem.tests, timeout=args.timeout)
        total += result.total
        if result.passed != result.total:
            failures.append({"id": problem.id, "title": problem.title,
                             "failed_cases": [case.name for case in result.cases if not case.passed]})
    candidate_a, candidate_b = compare(
        "def solve(data):\n    return data['value']",
        "def solve(data):\n    return 0",
        [TestCase("comparison sanity", {"value": 7}, 7)], timeout=args.timeout)
    comparison_ok = candidate_a.score == 1.0 and candidate_b.score == 0.0
    summary = {"benchmark_problems": len(BENCHMARKS), "reference_cases": total,
               "reference_failures": failures,
               "comparison_check": "passed" if comparison_ok else "failed"}
    print(json.dumps(summary, indent=2))
    return 0 if not failures and comparison_ok else 1


if __name__ == "__main__":
    sys.exit(main())
