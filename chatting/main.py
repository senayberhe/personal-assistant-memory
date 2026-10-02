import logging

from assistant.application import Application
from assistant.errors import (
    AssistantError,
    ConfigurationError,
)
from assistant.factory import ApplicationFactory
from config.logging_config import configure_logging
from config.settings import Settings

logger = logging.getLogger(__name__)


def main() -> None:

    application: Application | None = None

    try:
        settings = Settings.from_environment()

        configure_logging(
            environment=settings.environment,
            log_level=settings.log_level,
        )

        logger.info(
            "Building application."
        )

        factory = ApplicationFactory(
            settings=settings
        )

        application = factory.create()

        application.startup()

        application.run()

    except ConfigurationError as error:

        logger.error(
            "Configuration error: %s",
            error,
        )

        print(
            f"Configuration error: {error}"
        )

    except AssistantError as error:

        logger.exception(
            "Assistant error."
        )

        print(
            f"Assistant error: {error}"
        )

    except Exception:

        logger.exception(
            "Unexpected application failure."
        )

        raise

    finally:

        if application is not None:
            application.shutdown()


if __name__ == "__main__":
    main()
