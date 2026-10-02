import webbrowser

from services.url_security import validate_url


class BrowserService:

    def open_website(
        self,
        website: str,
    ) -> str:

        if not website:
            return (
                "Please specify "
                "a website."
            )

        if "://" not in website:
            website = (
                "https://"
                + website
            )

        try:
            website = validate_url(
                website
            )

        except ValueError as error:
            return f"I can't open that website. {error}"

        webbrowser.open(
            website
        )

        return (
            f"Opening {website}."
        )
