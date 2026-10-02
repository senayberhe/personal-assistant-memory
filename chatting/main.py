"""
Start the assistant.

    python main.py            # voice mode (microphone + speech)
    python main.py --text     # text chat in the terminal
"""

import argparse
import logging
import sys

from assistant.application import Application
from assistant.errors import AssistantError, ConfigurationError, StartupError
from assistant.factory import ApplicationFactory
from config.logging_config import configure_logging
from config.settings import PROJECT_ROOT, Settings

logger = logging.getLogger(__name__)

LOG_FILE = PROJECT_ROOT / "logs" / "assistant.log"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Voice and text assistant with long-term memory.",
    )

    mode = parser.add_mutually_exclusive_group()

    mode.add_argument(
        "--text",
        dest="interface",
        action="store_const",
        const="text",
        help="chat by typing in the terminal",
    )

    mode.add_argument(
        "--voice",
        dest="interface",
        action="store_const",
        const="voice",
        help="talk using the microphone (default)",
    )

    parser.set_defaults(interface="voice")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the assistant. Returns the process exit code."""

    args = parse_args(argv)
    application: Application | None = None

    try:
        settings = Settings.from_environment()

        configure_logging(
            environment=settings.environment,
            log_level=settings.log_level,
            log_file=LOG_FILE,
            # In the chat, only problems are printed; everything
            # else goes to the log file.
            console_level="WARNING" if args.interface == "text" else None,
        )

        logger.info("Building application (interface=%s).", args.interface)

        application = ApplicationFactory(settings=settings).create(
            interface=args.interface
        )

        application.startup()
        application.run()

        return 0

    except ConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        print(
            "Copy chatting/.env.example to chatting/.env and fill in "
            "your OPENAI_API_KEY.",
            file=sys.stderr,
        )
        return 2

    except StartupError as error:
        print(f"Could not start: {error}", file=sys.stderr)

        if args.interface == "voice":
            print(
                "No microphone? Try text mode: python main.py --text",
                file=sys.stderr,
            )

        return 1

    except AssistantError as error:
        logger.exception("Assistant error.")
        print(f"Assistant error: {error}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        return 130

    finally:
        if application is not None:
            application.shutdown()


if __name__ == "__main__":
    sys.exit(main())
