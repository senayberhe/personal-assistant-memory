from unittest.mock import MagicMock

import pytest

from assistant.application import Application


def test_application_starts():

    assistant = MagicMock()

    health_checker = MagicMock()

    health_checker.run.return_value = []

    application = Application(
        assistant=assistant,
        health_checker=health_checker,
    )

    application.startup()

    assert application.is_running is True


def test_application_shutdown():

    assistant = MagicMock()

    health_checker = MagicMock()

    health_checker.run.return_value = []

    application = Application(
        assistant=assistant,
        health_checker=health_checker,
    )

    application.startup()
    application.shutdown()

    assert application.is_running is False


def test_application_cannot_run_before_start():

    assistant = MagicMock()

    health_checker = MagicMock()

    application = Application(
        assistant=assistant,
        health_checker=health_checker,
    )

    with pytest.raises(RuntimeError):

        application.run()