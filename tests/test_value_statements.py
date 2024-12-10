import pytest

from mpd_inspector.value_statements import StatedValue


class TestValueStatements:
    def test_eq(self):
        assert StatedValue("foo") == "foo"

    def test_add(self):
        assert StatedValue("foo") + "bar" == "foobar"
        assert StatedValue(5) + 4 == 9

    def test_isinstance(self):
        val = StatedValue("foo")
        assert isinstance(val, StatedValue)
        assert isinstance(val.value, str)
        # assert type(val) == str
