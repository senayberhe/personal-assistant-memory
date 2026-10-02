import logging
import subprocess
import tempfile

from gtts import gTTS

logger = logging.getLogger(__name__)


class TTSService:

    def __init__(
        self,
        language: str = "en",
    ):
        self.language = language

    def speak(
        self,
        text: str,
    ) -> None:

        if not text:
            return

        print(
            f"Assistant: {text}"
        )

        try:
            self._speak_with_gtts(text)

        except Exception:
            # gTTS needs the internet; fall back to
            # the built-in macOS voice.
            logger.warning(
                "gTTS failed, falling back to 'say'.",
                exc_info=True,
            )

            subprocess.run(
                ["say", text],
                check=False,
            )

    def _speak_with_gtts(
        self,
        text: str,
    ) -> None:

        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
        ) as audio_file:

            gTTS(
                text=text,
                lang=self.language,
            ).write_to_fp(audio_file)

            audio_file.flush()

            subprocess.run(
                ["afplay", audio_file.name],
                check=True,
            )
