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

    @classmethod
    def _missing_(cls, value):
        if value is None:
            return None
        return super()._missing_(
            value
        )  # Still raise ValueError for other invalid values
