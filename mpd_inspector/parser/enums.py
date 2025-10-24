import enum


class PresentationType(enum.Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"


class PeriodType(enum.Enum):
    # As per 5.3.2.1 in ISO/IEC 23009-1 Part 1
    REGULAR = "Regular Period"
    EARLY_AVAILABLE = "Early Available Period"
    EARLY_TERMINATED = "Early Terminated Period"


class AddressingMode(enum.Enum):
    EXPLICIT = "explicit"
    INDEXED = "indexed"
    SIMPLE = "simple"


class TemplateVariable(enum.Enum):
    NUMBER = "$Number$"
    TIME = "$Time$"


class ContentType(enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    APPLICATION = "application"
    FONT = "font"
    UNSPECIFIED = "unspecified"
    SUBTITLE = "subtitle"

    @classmethod
    def from_value(cls, val):
        if val is None:
            return None
        try:
            # Attempt to create the enum member using the standard constructor.
            # This will correctly find existing members like ContentType("text")
            # or raise ValueError for unknown string values like ContentType("invalid").
            return cls(val)
        except ValueError:
            # Propagate the ValueError if 'val' is an invalid (non-None) value.
            # This maintains the behavior where parsing an invalid string errors out.
            raise
