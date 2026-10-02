"""Short-term conversation history sent to the model."""


class ConversationMemory:

    def __init__(
        self,
        max_messages: int = 20,
    ):
        self.messages: list[dict] = []
        self.max_messages = max_messages

    def add(
        self,
        message: dict,
    ) -> None:

        self.messages.append(
            message
        )

        if (
            len(self.messages)
            > self.max_messages
        ):
            self.messages = (
                self.messages[
                    -self.max_messages:
                ]
            )

    def add_user_message(
        self,
        content: str,
    ) -> None:

        self.add(
            {
                "role": "user",
                "content": content,
            }
        )

    def add_assistant_message(
        self,
        content: str,
    ) -> None:

        self.add(
            {
                "role": "assistant",
                "content": content,
            }
        )

    def get_messages(
        self,
    ) -> list[dict]:

        return list(self.messages)

    def clear(self) -> None:
        self.messages.clear()
