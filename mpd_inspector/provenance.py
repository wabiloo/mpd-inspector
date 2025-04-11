from enum import Enum, auto


class ValueProvenance(Enum):
    """Enum representing the origin/source of a value in the MPD inspector."""

    EXPLICIT = auto()  # Value is explicitly set in the MPD
    DEFAULT = auto()  # Value is a default when not specified
    DERIVED = auto()  # Value is calculated from other values
    INHERITED = auto()  # Value is inherited from a parent element
