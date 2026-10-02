import logging

import speech_recognition as sr

logger = logging.getLogger(__name__)


class SpeechService:

    def __init__(
        self,
        timeout: int = 5,
        phrase_time_limit: int = 8,
        ambient_noise_duration: int = 1,
    ):

        self.timeout = timeout

        self.phrase_time_limit = (
            phrase_time_limit
        )

        self.ambient_noise_duration = (
            ambient_noise_duration
        )

        self.recognizer = (
            sr.Recognizer()
        )

    def health_check(self) -> bool:

        try:

            with sr.Microphone():
                pass

            return True

        except (OSError, AttributeError):
            # AttributeError: PyAudio is not installed.
            return False

    def calibrate(self) -> None:

        with sr.Microphone() as source:

            print(
                "Calibrating microphone..."
            )

            self.recognizer.adjust_for_ambient_noise(
                source,
                duration=(
                    self.ambient_noise_duration
                ),
            )

        print(
            "Microphone ready."
        )

    def listen(self) -> str | None:

        try:

            with sr.Microphone() as source:

                print(
                    "\nListening..."
                )

                audio = (
                    self.recognizer.listen(
                        source,
                        timeout=self.timeout,
                        phrase_time_limit=(
                            self.phrase_time_limit
                        ),
                    )
                )

        except sr.WaitTimeoutError:

            print(
                "I didn't hear anything."
            )

            return None

        except OSError as error:

            logger.exception(
                "Microphone error: %s",
                error,
            )

            return None

        try:

            text = (
                self.recognizer
                .recognize_google(audio)
            )

            text = text.strip()

            print(
                f"You: {text}"
            )

            return text

        except sr.UnknownValueError:

            print(
                "I couldn't understand that."
            )

        except sr.RequestError as error:

            logger.exception(
                "Speech recognition error: %s",
                error,
            )

            print(
                "Speech recognition "
                "service is unavailable."
            )

        return None
