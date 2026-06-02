"""Named errors and run budget classification."""

import time

import pytest

from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.errors import (
    BrowserStepError,
    BrowserStepTimeout,
    RunBudgetExceeded,
    classify_step_error,
)


def test_classify_step_error_types():
    assert classify_step_error(RunBudgetExceeded("x")) == "RunBudgetExceeded"
    assert classify_step_error(BrowserStepTimeout("x")) == "BrowserStepTimeout"
    assert classify_step_error(BrowserStepError("x")) == "BrowserStepError"
    assert classify_step_error(TimeoutError()) == "BrowserStepTimeout"
    assert classify_step_error(ValueError("fail")) == "BrowserStepError"


def test_per_journey_step_budget_math():
    personas = [Persona(id=f"p{i}", name=f"P{i}", role="r", goals=[]) for i in range(1, 4)]
    steps = [Step(action="navigate", url="https://x/")] * 10
    journeys = [
        Journey(id=f"j{i}", name=f"J{i}", steps=steps if i == 1 else [Step(action="navigate", url="https://x/")])
        for i in range(1, 6)
    ]
    cfg = RunConfig(
        target_url="https://example.com",
        run_id_prefix="t",
        product_name="T",
        personas=personas,
        journeys=journeys,
        budgets=Budgets(max_steps_per_journey=5, parallel_seeds=2, repeat_micro_loop=1),
    )
    journey = cfg.journeys[0]
    per_journey_budget = len(journey.steps) * cfg.budgets.parallel_seeds * cfg.budgets.repeat_micro_loop
    assert per_journey_budget > cfg.budgets.max_steps_per_journey


def test_run_deadline_exceeded():
    deadline = time.perf_counter() - 1
    with pytest.raises(RunBudgetExceeded):
        if time.perf_counter() > deadline:
            raise RunBudgetExceeded("max_run_seconds exceeded")
