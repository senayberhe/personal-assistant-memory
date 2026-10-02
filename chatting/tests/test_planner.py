from assistant.planner import (
    PlanStep,
    PlanValidator,
)


def test_valid_plan():

    plan = [
        PlanStep(
            step_id="search",
            description="Search Google",
            tool_name="search_google",
            arguments={
                "query": "Python"
            },
            depends_on=[],
        )
    ]

    validator = PlanValidator()

    result = validator.validate(
        plan,
        {"search_google"},
    )

    assert result is True


def test_missing_dependency():

    plan = [
        PlanStep(
            step_id="open",
            description="Open website",
            tool_name="open_website",
            arguments={
                "website": "github.com"
            },
            depends_on=[
                "missing_step"
            ],
        )
    ]

    validator = PlanValidator()

    result = validator.validate(
        plan,
        {"open_website"},
    )

    assert result is False