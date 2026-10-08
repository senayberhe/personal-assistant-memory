import main
import pytest

from assistant.errors import StartupError
from config.settings import PROJECT_ROOT, resolve_project_path


def test_default_interface_is_voice():
    assert main.parse_args([]).interface == "voice"


def test_text_flag():
    assert main.parse_args(["--text"]).interface == "text"


def test_text_and_voice_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        main.parse_args(["--text", "--voice"])


def test_missing_api_key_gives_helpful_message(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "")

    assert main.main(["--text"]) == 2

    error = capsys.readouterr().err

    assert "OPENAI_API_KEY" in error
    assert ".env.example" in error


def test_failed_startup_suggests_text_mode(monkeypatch, capsys):
    class FailingApplication:
        def startup(self):
            raise StartupError("Startup health checks failed: Microphone is unavailable.")

        def shutdown(self):
            pass

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        main.ApplicationFactory,
        "create",
        lambda self, interface: FailingApplication(),
    )
    monkeypatch.setattr(main, "configure_logging", lambda **kwargs: None)

    assert main.main([]) == 1
    assert "python main.py --text" in capsys.readouterr().err


def test_relative_paths_resolve_to_project_folder(tmp_path):
    assert resolve_project_path("data/memory") == str(PROJECT_ROOT / "data/memory")
    assert resolve_project_path(str(tmp_path)) == str(tmp_path)
