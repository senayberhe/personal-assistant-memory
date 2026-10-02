import logging

from assistant.errors import (
    PermissionDeniedError,
    ToolError,
)

logger = logging.getLogger(__name__)


class ToolExecutor:

    def __init__(
        self,
        registry,
        permission_manager,
    ):
        self.registry = registry
        self.permission_manager = (
            permission_manager
        )

    def execute(
        self,
        tool_name: str,
        arguments: dict,
    ) -> str:

        # -------------------------
        # Find tool
        # -------------------------

        tool = self.registry.get(
            tool_name
        )

        if tool is None:

            raise ToolError(
                f"Unknown tool: {tool_name}"
            )

        # -------------------------
        # Permission
        # -------------------------

        try:

            allowed = (
                self.permission_manager
                .confirm(tool)
            )

        except Exception as error:

            raise PermissionDeniedError(
                "Permission check failed."
            ) from error

        if not allowed:

            logger.info(
                "Tool denied: %s",
                tool_name,
            )

            raise PermissionDeniedError(
                f"Permission denied for "
                f"'{tool_name}'."
            )

        # -------------------------
        # Validate arguments
        # -------------------------

        validated_arguments = arguments

        if tool.argument_model is not None:

            try:

                model = (
                    tool.argument_model(
                        **arguments
                    )
                )

                validated_arguments = (
                    model.model_dump()
                )

            except Exception as error:

                raise ToolError(
                    f"Invalid arguments "
                    f"for '{tool_name}'."
                ) from error

        # -------------------------
        # Execute tool
        # -------------------------

        try:

            logger.info(
                "Executing tool=%s",
                tool_name,
            )

            result = tool.handler(
                **validated_arguments
            )

            logger.info(
                "Tool completed=%s",
                tool_name,
            )

            return str(result)

        except Exception as error:

            logger.exception(
                "Tool execution failed=%s",
                tool_name,
            )

            raise ToolError(
                f"Tool '{tool_name}' failed."
            ) from error