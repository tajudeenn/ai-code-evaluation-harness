"""Core evaluation logic for the AI Code Evaluation Harness."""
from __future__ import annotations

import ast
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TestCase:
    name: str
    input: Any
    expected: Any
    edge_case: bool = False


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    category: str
    prompt: str
    reference_solution: str
    tests: tuple[TestCase, ...]


@dataclass
class CaseResult:
    name: str
    passed: bool
    expected: Any
    actual: Any = None
    error: str | None = None
    edge_case: bool = False


@dataclass
class Evaluation:
    status: str
    score: float
    passed: int
    total: int
    edge_passed: int
    edge_total: int
    runtime_ms: float | None
    cases: list[CaseResult]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


BLOCKED_IMPORTS = {"subprocess", "socket", "ctypes", "multiprocessing", "requests", "urllib", "http", "ftplib", "telnetlib", "shutil", "pathlib", "importlib"}
BLOCKED_CALLS = {"eval", "exec", "compile", "__import__", "breakpoint"}


def validate_candidate(source: str) -> str | None:
    """Apply defense-in-depth checks. This is not a secure sandbox."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return f"Syntax error on line {exc.lineno}: {exc.msg}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            blocked = next((name for name in names if name in BLOCKED_IMPORTS), None)
            if blocked:
                return f"Import of '{blocked}' is blocked by the evaluation policy."
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
            return f"Use of '{node.func.id}' is blocked by the evaluation policy."
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            return "Names beginning with double underscores are blocked by the evaluation policy."
    return None


def values_equal(actual: Any, expected: Any, *, abs_tol: float = 1e-7, rel_tol: float = 1e-7) -> bool:
    if isinstance(expected, bool):
        return actual is expected
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isclose(float(actual), float(expected), abs_tol=abs_tol, rel_tol=rel_tol)
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(values_equal(a, e, abs_tol=abs_tol, rel_tol=rel_tol) for a, e in zip(actual, expected))
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(values_equal(actual[k], expected[k], abs_tol=abs_tol, rel_tol=rel_tol) for k in expected)
    return type(actual) is type(expected) and actual == expected


def _run_one(source: str, case: TestCase, timeout: float) -> tuple[Any, str | None, float]:
    # Candidate is isolated to a fresh interpreter, temporary working directory,
    # minimal environment, stdin/stdout JSON protocol, and hard timeout.
    runner = r'''import json, math, sys, socket
socket.socket = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network disabled"))
payload=json.loads(sys.stdin.read())
def safe_import(name, *args, **kwargs):
    if name == "math": return math
    raise ImportError("only the math module is available")
scope={"__builtins__": {"__import__":safe_import,"abs":abs,"all":all,"any":any,"bool":bool,"dict":dict,"enumerate":enumerate,"Exception":Exception,"float":float,"int":int,"len":len,"list":list,"map":map,"max":max,"min":min,"pow":pow,"print":print,"range":range,"round":round,"set":set,"sorted":sorted,"str":str,"sum":sum,"tuple":tuple,"zip":zip,"ValueError":ValueError,"TypeError":TypeError,"ZeroDivisionError":ZeroDivisionError}, "math": math}
exec(compile(payload["source"], "<candidate>", "exec"), scope, scope)
if not callable(scope.get("solve")): raise TypeError("Candidate must define solve(data)")
result=scope["solve"](payload["input"])
print(json.dumps({"result":result}, allow_nan=False))
'''
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=".code_eval_", dir=Path(__file__).parent, ignore_cleanup_errors=True) as tmp:
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-S", "-c", runner], input=json.dumps({"source": source, "input": case.input}),
                capture_output=True, text=True, timeout=timeout, cwd=tmp,
                env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"},
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            elapsed = (time.perf_counter() - start) * 1000
            if completed.returncode:
                detail = completed.stderr.strip().splitlines()
                return None, (detail[-1] if detail else f"Process exited with code {completed.returncode}"), elapsed
            try:
                return json.loads(completed.stdout.strip().splitlines()[-1])["result"], None, elapsed
            except (ValueError, KeyError, IndexError):
                return None, "Output must be a JSON-serializable return value from solve(data).", elapsed
        except subprocess.TimeoutExpired:
            return None, f"Timed out after {timeout:g} seconds.", (time.perf_counter() - start) * 1000
        except (OSError, TypeError, ValueError) as exc:
            return None, str(exc), (time.perf_counter() - start) * 1000


def evaluate(source: str, tests: tuple[TestCase, ...] | list[TestCase], timeout: float = 2.0) -> Evaluation:
    issue = validate_candidate(source)
    if issue:
        return Evaluation("rejected", 0.0, 0, len(tests), 0, sum(t.edge_case for t in tests), None, [], issue)
    cases: list[CaseResult] = []
    durations: list[float] = []
    for test in tests:
        actual, error, elapsed = _run_one(source, test, timeout)
        durations.append(elapsed)
        passed = error is None and values_equal(actual, test.expected)
        cases.append(CaseResult(test.name, passed, test.expected, actual, error, test.edge_case))
    passed = sum(case.passed for case in cases)
    edge = [case for case in cases if case.edge_case]
    return Evaluation("complete", passed / len(tests) if tests else 0.0, passed, len(tests), sum(c.passed for c in edge), len(edge), sum(durations), cases,
                      "All test cases passed." if passed == len(tests) else f"{len(tests)-passed} test case(s) failed.")


def compare(source_a: str, source_b: str, tests: tuple[TestCase, ...] | list[TestCase], timeout: float = 2.0) -> tuple[Evaluation, Evaluation]:
    return evaluate(source_a, tests, timeout), evaluate(source_b, tests, timeout)
