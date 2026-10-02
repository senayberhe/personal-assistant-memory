import webbrowser

from urllib.parse import quote_plus


class SearchService:

    def google(
        self,
        query: str,
    ) -> str:

        if not query:
            return (
                "Please tell me "
                "what you want to search for."
            )

        encoded_query = quote_plus(
            query
        )

        url = (
            "https://www.google.com/search"
            f"?q={encoded_query}"
        )

        webbrowser.open(url)

        return (
            f"Searching Google for "
            f"{query}."
        )

    def youtube(
        self,
        query: str,
    ) -> str:

        if not query:
            return (
                "Please tell me "
                "what you want to search for."
            )

        encoded_query = quote_plus(
            query
        )

        url = (
            "https://www.youtube.com/results"
            f"?search_query={encoded_query}"
        )

        webbrowser.open(url)

        return (
            f"Searching YouTube for "
            f"{query}."
        )