from enum import Enum


class MemoryResolution(Enum):
    """
    Describes what should happen to a new memory.
    """
    CREATE = "create"
    UPDATE = "update"
    IGNORE = "ignore"
