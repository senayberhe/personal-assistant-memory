import logging

from assistant.errors import (
    PermissionDeniedError,
    ToolError,
)
from assistant.observability import (
    request_context,
)

logger = logging.getLogger(__name__)


class VoiceAssistant:

    def __init__(
        self,
        speech_service,
        agent,
        tts_service,
    ):
        self.speech = speech_service
        self.agent = agent
        self.tts = tts_service
        self.running = True

    def run(self) -> None:

        self.speech.calibrate()

        self.tts.speak(
            "Voice assistant is ready."
        )

        while self.running:

            text = self.speech.listen()

            if not text:
                continue

            if self.is_exit_command(text):

                self.tts.speak(
                    "Goodbye."
                )

                self.running = False
                break

            try:

                with request_context():

                    logger.info(
                        "Processing request."
                    )

                    response = (
                        self.agent.run(text)
                    )

                    self.tts.speak(
                        response
                    )

                    logger.info(
                        "Request completed."
                    )

            except PermissionDeniedError:

                logger.info(
                    "User denied tool permission."
                )

                self.tts.speak(
                    "Okay, I won't do that."
                )

            except ToolError:

                logger.exception(
                    "Tool execution failed."
                )

                self.tts.speak(
                    "I couldn't complete "
                    "that action."
                )

            except Exception:

                logger.exception(
                    "Unexpected assistant error."
                )

                self.tts.speak(
                    "Something unexpected "
                    "went wrong."
                )

    @staticmethod
    def is_exit_command(
        text: str,
    ) -> bool:

        normalized = (
            text.lower().strip()
        )

        return normalized in {
            "exit",
            "quit",
            "stop listening",
            "goodbye",
        }
