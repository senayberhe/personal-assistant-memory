from collections.abc import Callable

from assistant.tools.security import SecurityPolicy


def console_confirm(question: str) -> bool:
    """Ask a yes/no question in the terminal. Anything but yes is no."""

    answer = input(f"\n{question} [y/N]: ")

    return answer.strip().lower() in {"y", "yes"}


class PermissionManager:
    """
    Decides whether a tool may run.

    Blocked risk levels are always refused. Risky tools need the
    user's explicit confirmation through `confirm`, which can be
    swapped for a different UI (for example the rich text UI).
    """

    def __init__(
        self,
        security_policy: SecurityPolicy,
        confirm: Callable[[str], bool] = console_confirm,
    ):
        self.security_policy = security_policy
        self.confirm_with_user = confirm

    def confirm(self, tool) -> bool:

        if not self.security_policy.is_allowed(tool.risk_level):
            return False

        requires_confirmation = (
            tool.requires_confirmation
            or self.security_policy.requires_confirmation(tool.risk_level)
        )

        if not requires_confirmation:
            return True

        return self.confirm_with_user(
            f"This action is classified as "
            f"{tool.risk_level.name.lower()} risk.\n"
            f"Run '{tool.name}'?"
        )
