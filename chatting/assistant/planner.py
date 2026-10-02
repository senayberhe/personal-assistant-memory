from dataclasses import dataclass


@dataclass
class PlanStep:

    step_id: str

    description: str

    tool_name: str

    arguments: dict

    depends_on: list[str]


class PlanValidator:

    def validate(
        self,
        plan: list[PlanStep],
        available_tools: set[str],
    ) -> bool:

        step_ids = {
            step.step_id
            for step in plan
        }

        for step in plan:

            # -------------------------
            # Check tool
            # -------------------------

            if (
                step.tool_name
                not in available_tools
            ):
                return False

            # -------------------------
            # Check dependencies
            # -------------------------

            for dependency in (
                step.depends_on
            ):

                if dependency not in step_ids:
                    return False

        return True


class RuleBasedPlanner:

    def create_plan(
        self,
        goal: str,
    ) -> list[PlanStep]:

        normalized = (
            goal.lower().strip()
        )

        if "search google" in normalized:

            return [
                PlanStep(
                    step_id="search",
                    description=(
                        "Search Google"
                    ),
                    tool_name="search_google",
                    arguments={
                        "query": goal
                    },
                    depends_on=[],
                )
            ]

        return []