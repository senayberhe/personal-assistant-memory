class MemoryExtractor:
    def extract(self, user_text: str) -> list[dict]:
        text = user_text.lower().strip()

        memories = []

        if "my favorite language is" in text:
            memories.append({
                "content": user_text,
                "memory_type": "preference",
            })

        if "i prefer" in text:
            memories.append({
                "content": user_text,
                "memory_type": "preference",
            })

        if "remember that" in text:
            memories.append({
                "content": user_text,
                "memory_type": "instruction",
            })

        return memories