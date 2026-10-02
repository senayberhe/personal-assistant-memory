from enum import Enum


class MemoryResolution(Enum):
    """
    Describes how a new memory relates to an
    existing memory.
    """
    CREATE = "create"
    UPDATE = "update"
    IGNORE = "ignore"
    CONTRADICT = "contradict"
    UNRELATED = "unrelated"
