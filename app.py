import json

import streamlit as st

from benchmarks import BENCHMARKS
from harness import TestCase, compare, evaluate

st.set_page_config(page_title="BioCode Eval", page_icon="🧪", layout="wide")
st.title("🧪 BioCode Eval")
st.caption("A transparent, test-driven review harness for AI-generated scientific code")


def report_context(result, *, task_id, task_title, prompt, candidate):
    report = result.to_dict()
    report["task"] = {"id": task_id, "title": task_title, "prompt": prompt}
    report["candidate"] = candidate
    return report

with st.sidebar:
    st.header("Evaluation setup")
    selected = st.selectbox("Starter benchmark", BENCHMARKS, format_func=lambda p: f"{p.id} · {p.title}")
    timeout = st.slider("Time limit per test (seconds)", 0.25, 5.0, 2.0, 0.25)
    st.caption("Each test runs in its own fresh Python process.")

st.subheader(f"{selected.id} · {selected.title}")
st.markdown(f"**{selected.category}**  \n{selected.prompt}")
with st.expander("View evaluation cases"):
    st.json([{"name": t.name, "input": t.input, "expected": t.expected, "edge_case": t.edge_case} for t in selected.tests])

st.warning(
    "Prototype safety notice: candidate code runs in a separate Python process with "
    "best-effort restrictions, not a secure sandbox. Do not submit secrets, private "
    "datasets, or other sensitive information."
)

tab_single, tab_compare, tab_custom = st.tabs(["Evaluate one", "Compare two", "Custom task"])
with tab_single:
    starter = "def solve(data):\n    # Return the answer for the provided input dictionary\n    return None"
    code = st.text_area("Paste candidate Python code (define solve(data))", value=starter, height=260, key="single_code")
    if st.button("Run evaluation", type="primary", key="run_single"):
        result = evaluate(code, selected.tests, timeout)
        st.session_state["last_result"] = report_context(
            result, task_id=selected.id, task_title=selected.title,
            prompt=selected.prompt, candidate="Candidate")

with tab_compare:
    left, right = st.columns(2)
    code_a = left.text_area("Candidate A", value=selected.reference_solution, height=260, key="candidate_a")
    code_b = right.text_area("Candidate B", value=starter, height=260, key="candidate_b")
    if st.button("Compare on same tests", type="primary"):
        outcomes = compare(code_a, code_b, selected.tests, timeout)
        st.session_state["comparison"] = [
            report_context(r, task_id=selected.id, task_title=selected.title,
                           prompt=selected.prompt, candidate=f"Candidate {label}")
            for r, label in zip(outcomes, ("A", "B"))]

with tab_custom:
    st.markdown("For a task outside the benchmark, describe the problem and provide JSON test cases with `name`, `input`, `expected`, and optional `edge_case` fields.")
    custom_prompt = st.text_area("Problem statement", "Write a Python function solve(data) for this task.", key="custom_prompt")
    default_cases = '[{"name":"example","input":{"value":2},"expected":2}]'
    raw_cases = st.text_area("Test cases (JSON)", default_cases, height=150)
    custom_code = st.text_area("Candidate code", starter, height=220, key="custom_code")
    if st.button("Evaluate custom task", type="primary"):
        try:
            parsed = json.loads(raw_cases)
            tests = [TestCase(str(c.get("name", f"case {i+1}")), c["input"], c["expected"], bool(c.get("edge_case", False))) for i, c in enumerate(parsed)]
            if not isinstance(parsed, list) or not tests:
                raise ValueError("Provide at least one test case as a JSON array.")
            st.session_state["custom_result"] = report_context(
                evaluate(custom_code, tests, timeout), task_id="CUSTOM",
                task_title="Custom task", prompt=custom_prompt, candidate="Candidate")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            st.error(f"Could not read those test cases: {exc}")


def show_result(result):
    score = result["score"]
    task = result.get("task", {})
    st.caption(f"{result.get('candidate', 'Candidate')} · {task.get('id', '')} · {task.get('title', '')}")
    if task.get("prompt"):
        st.markdown(task["prompt"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Correctness", f"{score:.0%}")
    c2.metric("Tests passed", f"{result['passed']} / {result['total']}")
    c3.metric("Edge cases", f"{result['edge_passed']} / {result['edge_total']}")
    c4.metric("Runtime", f"{result['runtime_ms']:.1f} ms" if result["runtime_ms"] is not None else "—")
    st.info(result["message"])
    if result["cases"]:
        st.dataframe([{"Test": c["name"], "Result": "PASS" if c["passed"] else "FAIL", "Edge case": c["edge_case"], "Expected": c["expected"], "Actual": c["actual"], "Error": c["error"]} for c in result["cases"]], use_container_width=True, hide_index=True)
    download_key = f"download-report-{task.get('id', 'task')}-{result.get('candidate', 'candidate').lower().replace(' ', '-')}"
    filename = f"{task.get('id', 'evaluation').lower()}-{result.get('candidate', 'candidate').lower().replace(' ', '-')}-report.json"
    st.download_button("Download report JSON", json.dumps(result, indent=2), filename, "application/json", key=download_key)


if "last_result" in st.session_state:
    st.divider(); st.subheader("Evaluation report"); show_result(st.session_state["last_result"])
if "custom_result" in st.session_state:
    st.divider(); st.subheader("Custom task report"); show_result(st.session_state["custom_result"])
if "comparison" in st.session_state:
    st.divider(); st.subheader("Side-by-side comparison")
    ca, cb = st.columns(2)
    with ca: st.markdown("### Candidate A"); show_result(st.session_state["comparison"][0])
    with cb: st.markdown("### Candidate B"); show_result(st.session_state["comparison"][1])

with st.expander("What this report measures"):
    st.markdown("Correctness is the fraction of visible tests passed; edge-case coverage is shown separately. Runtime is the sum of per-test subprocess wall times and includes process startup overhead. Style, clarity, scientific validity beyond the supplied tests, and maintainability require a human rubric review unless you configure a separate evaluator. This starter does not make automated style claims.")
