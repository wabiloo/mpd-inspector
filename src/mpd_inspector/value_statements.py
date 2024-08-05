class StatedValue:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        if isinstance(other, StatedValue):
            return self.value + other.value
        return self.value + other

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, StatedValue):
            return self.value - other.value
        return self.value - other

    def __rsub__(self, other):
        if isinstance(other, StatedValue):
            return other.value - self.value
        return other - self.value

    def __mul__(self, other):
        if isinstance(other, StatedValue):
            return self.value * other.value
        return self.value * other

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, StatedValue):
            return self.value / other.value
        return self.value / other

    def __rtruediv__(self, other):
        if isinstance(other, StatedValue):
            return other.value / self.value
        return other / self.value

    def __eq__(self, other):
        if isinstance(other, StatedValue):
            return self.value == other.value
        return self.value == other

    def __lt__(self, other):
        if isinstance(other, StatedValue):
            return self.value < other.value
        return self.value < other

    def __le__(self, other):
        if isinstance(other, StatedValue):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other):
        if isinstance(other, StatedValue):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other):
        if isinstance(other, StatedValue):
            return self.value >= other.value
        return self.value >= other

    def __repr__(self):
        return f"StatedValue({self.value})"


class ExplicitValue(StatedValue):

    def __repr__(self):
        return f"ExplicitValue({self.value})"


class DefaultValue(StatedValue):

    def __repr__(self):
        return f"DefaultValue({self.value})"


class ImplicitValue(StatedValue):

    def __repr__(self):
        return f"ImplicitValue({self.value})"
