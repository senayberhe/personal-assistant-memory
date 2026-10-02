import logging


logger = logging.getLogger(__name__)


class Application:

    def __init__(
        self,
        assistant,
        health_checker,
    ):
        self.assistant = assistant
        self.health_checker = health_checker
        self.started = False

    @property
    def is_running(self) -> bool:
        return self.started

    def startup(self) -> None:

        logger.info(
            "Starting voice assistant."
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

        if not all(
            result.healthy
            for result in results
        ):
            raise RuntimeError(
                "Startup health checks failed."
            )

        self.started = True

        logger.info(
            "Voice assistant started."
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
            "Shutting down voice assistant."
        )

        self.started = False

        logger.info(
            "Voice assistant stopped."
        )