import subprocess


class ApplicationService:

    def open_chrome(self) -> str:

        subprocess.run(
            [
                "open",
                "-a",
                "Google Chrome",
            ],
            check=False,
        )

        return (
            "Opening Google Chrome."
        )

    def open_safari(self) -> str:

        subprocess.run(
            [
                "open",
                "-a",
                "Safari",
            ],
            check=False,
        )

        return (
            "Opening Safari."
        )

    def open_terminal(self) -> str:

        subprocess.run(
            [
                "open",
                "-a",
                "Terminal",
            ],
            check=False,
        )

        return (
            "Opening Terminal."
        )