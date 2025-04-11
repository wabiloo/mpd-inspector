import enum


class SpliceCommandType(enum.Enum):
    SPLICE_INSERT = 5
    TIME_SIGNAL = 6
    SPLICE_NULL = 7
    BANDWIDTH_RESERVATION = 8
    PRIVATE = 9
    SPLICE_SCHEDULE = 10

    def __str__(self):
        return f"{self.name.lower()} (0x{self.value:02x})"
