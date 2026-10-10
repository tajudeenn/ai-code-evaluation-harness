"""Validation helpers for user-defined benchmark cases."""
from __future__ import annotations

import json

from harness import TestCase


MAX_CUSTOM_CASES = 50
MAX_CUSTOM_JSON_CHARS = 100_000


def parse_custom_cases(raw: str) -> list[TestCase]:
    """Parse and validate the custom-task JSON without leaking shape errors."""
    if len(raw) > MAX_CUSTOM_JSON_CHARS:
        raise ValueError(f"Test-case JSON must be {MAX_CUSTOM_JSON_CHARS:,} characters or fewer.")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno}).") from exc
    if not isinstance(parsed, list):
        raise ValueError("Provide test cases as a JSON array.")
    if not parsed:
        raise ValueError("Provide at least one test case.")
    if len(parsed) > MAX_CUSTOM_CASES:
        raise ValueError(f"Provide no more than {MAX_CUSTOM_CASES} test cases per evaluation.")

    cases: list[TestCase] = []
    for index, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Test case {index} must be a JSON object.")
        missing = {"input", "expected"} - item.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"Test case {index} is missing required field(s): {fields}.")
        if "edge_case" in item and not isinstance(item["edge_case"], bool):
            raise ValueError(f"Test case {index} field 'edge_case' must be true or false.")
        name = item.get("name", f"case {index}")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Test case {index} field 'name' must be a non-empty string.")
        cases.append(TestCase(name.strip(), item["input"], item["expected"], item.get("edge_case", False)))
    return cases
