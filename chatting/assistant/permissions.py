from assistant.security import (
    SecurityPolicy,
)


class PermissionManager:

    def __init__(
        self,
        security_policy: SecurityPolicy,
    ):
        self.security_policy = security_policy

    def confirm(self, tool) -> bool:

        if not self.security_policy.is_allowed(
            tool.risk_level
        ):
            return False

        requires_confirmation = (
            tool.requires_confirmation
            or self.security_policy.requires_confirmation(
                tool.risk_level
            )
        )

        if not requires_confirmation:
            return True

        answer = input(
            f"\nThis action is classified as "
            f"{tool.risk_level.name.lower()} risk.\n"
            f"Run '{tool.name}'? [y/N]: "
        )

        return (
            answer.strip().lower()
            in {"y", "yes"}
        )
