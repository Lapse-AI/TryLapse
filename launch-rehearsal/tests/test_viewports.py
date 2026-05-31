"""Viewport profiles and journey budget scaling."""

from rehearse.dsl import Budgets, Journey, Persona, RunConfig, Step
from rehearse.viewports import normalize_viewports, VIEWPORT_PROFILES


def test_normalize_viewports_defaults():
    assert normalize_viewports(None) == ["desktop"]
    assert normalize_viewports([]) == ["desktop"]
    assert normalize_viewports(["mobile", "desktop", "bogus"]) == ["mobile", "desktop"]


def test_viewport_profiles_sizes():
    assert VIEWPORT_PROFILES["mobile"]["width"] == 390
    assert VIEWPORT_PROFILES["desktop"]["width"] == 1280


def test_journey_step_budget_scales_with_viewports():
    config = RunConfig(
        target_url="https://example.com",
        run_id_prefix="t",
        product_name="T",
        personas=[
            Persona(id="p1", name="A", role="r", goals=[]),
            Persona(id="p2", name="B", role="r", goals=[]),
            Persona(id="p3", name="C", role="r", goals=[]),
        ],
        journeys=[
            Journey(
                id="j1",
                name="One",
                steps=[Step(action="navigate", url="https://example.com/"), Step(action="wait", value="1")],
            ),
            Journey(id="j2", name="Two", steps=[]),
            Journey(id="j3", name="Three", steps=[]),
            Journey(id="j4", name="Four", steps=[]),
            Journey(id="j5", name="Five", steps=[]),
        ],
        budgets=Budgets(max_steps_per_journey=5),
        viewports=["desktop", "mobile"],
    )
    steps_per_journey = 2
    budget = steps_per_journey * config.budgets.parallel_seeds * config.budgets.repeat_micro_loop
    budget *= len(normalize_viewports(config.viewports))
    assert budget == 4
    assert budget <= config.budgets.max_steps_per_journey
