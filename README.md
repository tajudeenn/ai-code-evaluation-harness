# BioCode Eval — AI Code Evaluation Harness

A small portfolio project for evaluating AI-generated Python against reproducible tests. The starter benchmark contains 24 original quantitative science and biotechnology tasks, each with a reference solution and normal/edge-case examples. Use the app to evaluate one candidate, compare two candidates on identical cases, or define a small custom task using JSON inputs and expected outputs.

[![Tests](https://github.com/tajudeenn/ai-code-evaluation-harness/actions/workflows/tests.yml/badge.svg)](https://github.com/tajudeenn/ai-code-evaluation-harness/actions/workflows/tests.yml)

## Features

- Correctness score, per-case expected/actual values, edge-case score, and elapsed runtime.
- A focused biology/biotechnology benchmark: molarity, dilution, qPCR ΔΔCt, growth rates, Beer–Lambert, Michaelis–Menten, sequence utilities, calibration, statistics, and more.
- Candidate interface contract: Python source must define `solve(data)` and return a JSON-serializable value.
- Best-effort execution controls: fresh interpreter per test, isolated mode, no site initialization, temporary working directory, minimal environment, timeout, restricted builtins, a small import policy, and socket blocking.
- JSON report download and same-test candidate comparison.

## Setup

Python 3.10 or newer is recommended.

```powershell
cd ai-code-evaluation-harness
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Run the app:

```powershell
streamlit run app.py
```

Run the tests:

```powershell
python -m pytest
```

Run a dependency-free smoke check of all reference solutions and the comparison path (useful when pytest is not installed):

```powershell
python smoke_check.py
```

Choose **BIO03 · qPCR ΔΔCt** for a compact demo. The benchmark reference solution is prefilled in Compare Candidate A; leave the simple placeholder in Candidate B, then click **Compare on same tests**. To see custom task flow, submit one JSON case such as `[{"name":"example","input":{"value":2},"expected":2}]` and a `solve(data)` function returning `data["value"]`.

## Live demo

Try [BioCode Eval on Streamlit Community Cloud](https://ai-code-evaluation-harness-kktzxrrb4sbijq5kfik3xn.streamlit.app/). For the quickest walkthrough, select **BIO03 · qPCR ΔΔCt**, open **Compare two**, keep the reference solution in Candidate A, and compare it with the placeholder in Candidate B. The report shows per-case results, edge-case performance, runtime, and downloadable JSON reports. The custom-task form also accepts a JSON array of cases; malformed inputs are reported inline with a helpful validation message.

## Reading the report

Correctness is passed cases divided by total cases; floating point values use a small numeric tolerance. Edge cases are also counted separately. Runtime is the sum of per-case wall-clock times, including process startup overhead. Expected and actual values are displayed so failures are explainable. The report does not automatically grade style, clarity, or whether a scientifically plausible algorithm was chosen when the supplied examples are insufficient. Use the [human review rubric](review_rubric.md) for those dimensions, or connect a separately configured evaluator and disclose its role.

## Execution safety and limitations

**A subprocess is not a secure sandbox.** This app runs untrusted code, so use it only on a machine/container with no sensitive files or credentials. The policy checks and restricted child process are defense in depth, not a security boundary. Python introspection, interpreter vulnerabilities, resource exhaustion, platform behavior, and implementation mistakes may bypass controls. The timeout limits ordinary hangs, and socket use is blocked in the child, but this does not provide OS-level network isolation, filesystem isolation, syscall filtering, memory quotas, or robust process-tree containment.

For real multi-user or internet-facing use, run each evaluation in a disposable, unprivileged container or dedicated sandbox service with no network, read-only base filesystem, strict CPU/memory/PID limits, per-run storage, and enforced process cleanup. Keep secrets outside the evaluator. Do not expose this local prototype as a service that executes arbitrary public submissions.

## Project layout

- `app.py` — Streamlit interface.
- `harness.py` — case model, candidate policy checks, subprocess runner, scoring, comparison.
- `custom_cases.py` — clear validation for custom-task JSON with limits on payload size and case count.
- `benchmarks.py` — original benchmark prompts, reference solutions, and test cases.
- `tests/test_harness.py` — scoring, reference benchmark, policy, comparison, numeric tolerance, and timeout checks.
- `.github/workflows/tests.yml` — GitHub Actions workflow that installs development dependencies and runs pytest on pushes and pull requests.
- `smoke_check.py` — standard-library validation of all benchmark references and a comparison sanity check.
- `review_rubric.md` — manual rubric for scientific reasoning, edge cases, clarity, maintainability, and safety awareness.

## Publish with GitHub and Streamlit Community Cloud

1. Push this folder as a standalone GitHub repository (for example, `tajudeenn/ai-code-evaluation-harness`).
2. In Streamlit Community Cloud, create an app from that repository, select branch `main`, and set the main file to `app.py`.
3. Streamlit Community Cloud installs the app dependencies from `requirements.txt`; pytest stays in `requirements-dev.txt` for local development.

The demo runs user-provided Python code. Keep the limitations above in mind before sharing the public app; this prototype is intended for portfolio demonstration and controlled review, not as a production service for arbitrary public submissions.

## Extending the benchmark

Add a `Problem` in `benchmarks.py` with an unambiguous prompt, known-good reference solution, and multiple cases including edge cases. Keep the input/output contract JSON-compatible. Review reference implementations scientifically before using scores for hiring, grading, or model claims; the benchmark is a teaching/demo set, not a validated assessment instrument.
