import logging
from collections.abc import Callable

from assistant.errors import StartupError

logger = logging.getLogger(__name__)


class Application:

    def __init__(
        self,
        assistant,
        health_checker,
        shutdown_hooks: list[Callable[[], None]] | None = None,
    ):
        """
        assistant:
            The interface to run (voice loop or text chat);
            anything with a run() method.
        shutdown_hooks:
            Cleanup callbacks run once on shutdown.
        """

        self.assistant = assistant
        self.health_checker = health_checker
        self.shutdown_hooks = list(shutdown_hooks or [])
        self.started = False

    @property
    def is_running(self) -> bool:
        return self.started

    def startup(self) -> None:

        logger.info(
            "Starting assistant."
        )

        results = self.health_checker.run()

        for result in results:

            if result.healthy:
                logger.info(
                    "Health check passed: %s - %s",
                    result.name,
                    result.message,
                )

            else:
                logger.error(
                    "Health check failed: %s - %s",
                    result.name,
                    result.message,
                )

        failed = [
            result
            for result in results
            if not result.healthy
        ]

        if failed:
            raise StartupError(
                "Startup health checks failed: "
                + "; ".join(result.message for result in failed)
            )

        self.started = True

        logger.info(
            "Assistant started."
        )

    def run(self) -> None:

        if not self.started:
            raise RuntimeError(
                "Application has not been started."
            )

        self.assistant.run()

    def shutdown(self) -> None:

        if not self.started:
            return

        logger.info(
            "Shutting down assistant."
        )

        for hook in self.shutdown_hooks:
            try:
                hook()

            except Exception:
                logger.exception("Shutdown hook failed.")

        self.started = False

        logger.info(
            "Assistant stopped."
        )