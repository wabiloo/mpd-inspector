def cast_to_index(value, one_based=False) -> int:
    value = int(value)
    if one_based and value > 0:
        value -= 1
    return value


def cast_to_range(value, one_based=False, array_size=None) -> range | None:
    if ":" not in value:
        raise ValueError(f"Not a range expression: {value}")
    else:
        start, end = value.split(":")
        # allowing for empty start and end (e.g. ':10' and '10:')
        if start == "":
            start = 0
        if end == "":
            end = -1

        # attempting to cast to index
        start = cast_to_index(start, one_based)
        stop = cast_to_index(end, False)

        # adjusting for optional one-based indexing
        if one_based and start > 0:
            start -= 1

        # allowing negative indices to be used to select from the end of the array
        if start < 0:
            start = array_size + start
        if stop < 0:
            stop = array_size + stop + 1

        return range(start, stop)
