import enum


class SpliceCommandType(enum.Enum):
    SPLICE_INSERT = 5
    TIME_SIGNAL = 6

    def __str__(self):
        return f"{self.name.lower()} (0x{self.value:02x})"
