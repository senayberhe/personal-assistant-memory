from assistant.memory_model import Memory


def format_memory_context(
    memories: list[Memory],
) -> str:

    if not memories:
        return "No relevant memories were found."

    lines = [
        "Relevant memories:"
    ]

    for memory in memories:
        lines.append(
            f"- {memory.content}"
        )

    return "\n".join(lines)