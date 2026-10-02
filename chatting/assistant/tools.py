from pydantic import BaseModel, Field

from assistant.registry import Tool
from services.applications import ApplicationService
from services.browser import BrowserService
from services.search import SearchService


# -------------------------
# Argument Models
# -------------------------

class SearchArguments(BaseModel):
    query: str = Field(
        min_length=1
    )


class WebsiteArguments(BaseModel):
    website: str = Field(
        min_length=1
    )


# -------------------------
# Assistant Tools
# -------------------------

class AssistantTools:

    def __init__(self):
        self.applications = ApplicationService()
        self.browser = BrowserService()
        self.search = SearchService()

    def open_chrome(self) -> str:
        return self.applications.open_chrome()

    def open_safari(self) -> str:
        return self.applications.open_safari()

    def open_terminal(self) -> str:
        return self.applications.open_terminal()

    def open_website(
        self,
        website: str,
    ) -> str:
        return self.browser.open_website(
            website
        )

    def search_google(
        self,
        query: str,
    ) -> str:
        return self.search.google(
            query
        )

    def search_youtube(
        self,
        query: str,
    ) -> str:
        return self.search.youtube(
            query
        )

    def register_tools(
        self,
        registry,
    ) -> None:

        registry.register(
            Tool(
                name="open_chrome",
                description="Open Google Chrome.",
                handler=self.open_chrome,
            )
        )

        registry.register(
            Tool(
                name="open_safari",
                description="Open Safari.",
                handler=self.open_safari,
            )
        )

        registry.register(
            Tool(
                name="open_terminal",
                description="Open macOS Terminal.",
                handler=self.open_terminal,
                requires_confirmation=True,
            )
        )

        registry.register(
            Tool(
                name="open_website",
                description="Open a website.",
                handler=self.open_website,
                argument_model=WebsiteArguments,
            )
        )

        registry.register(
            Tool(
                name="search_google",
                description="Search Google.",
                handler=self.search_google,
                argument_model=SearchArguments,
            )
        )

        registry.register(
            Tool(
                name="search_youtube",
                description="Search YouTube.",
                handler=self.search_youtube,
                argument_model=SearchArguments,
            )
        )


# -------------------------
# OpenAI Tool Definitions
# -------------------------

def build_tool_definitions():

    return [

        {
            "type": "function",
            "name": "open_chrome",
            "description": "Open Google Chrome.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },

        {
            "type": "function",
            "name": "open_safari",
            "description": "Open Safari.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },

        {
            "type": "function",
            "name": "open_terminal",
            "description": "Open macOS Terminal.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },

        {
            "type": "function",
            "name": "open_website",
            "description": "Open a website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "website": {
                        "type": "string"
                    }
                },
                "required": ["website"],
                "additionalProperties": False,
            },
            "strict": True,
        },

        {
            "type": "function",
            "name": "search_google",
            "description": "Search Google.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "strict": True,
        },

        {
            "type": "function",
            "name": "search_youtube",
            "description": "Search YouTube.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]