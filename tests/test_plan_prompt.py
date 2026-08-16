from app.agent.plan_prompt import build_plan_prompt
from app.api.schemas import PlanRequest


def test_full_fields_all_appear():
    payload = PlanRequest(
        destination="Goa",
        starting_city="Mumbai",
        duration_days=3,
        budget="₹15000",
        preferences="vegetarian, prefers quiet places",
        session_id="s1",
    )
    prompt = build_plan_prompt(payload)
    assert "Destination: Goa" in prompt
    assert "Starting city: Mumbai" in prompt
    assert "Duration: 3 day(s)" in prompt
    assert "budget: ₹15000" in prompt
    assert "vegetarian, prefers quiet places" in prompt


def test_missing_destination_says_open_to_suggestion():
    prompt = build_plan_prompt(PlanRequest())
    assert "open to a suggestion" in prompt


def test_omits_unset_optional_fields():
    prompt = build_plan_prompt(PlanRequest(destination="Hampi"))
    assert "Starting city" not in prompt
    assert "Duration" not in prompt
    assert "budget" not in prompt


def test_never_asks_model_to_look_up_emergency_numbers():
    prompt = build_plan_prompt(PlanRequest(destination="Varkala"))
    assert "Do not look up emergency numbers yourself" in prompt


def test_instructs_no_unsupported_safety_claims():
    prompt = build_plan_prompt(PlanRequest())
    assert "unsupported claims" in prompt
