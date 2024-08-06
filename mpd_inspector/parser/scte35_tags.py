from functools import cached_property
from .mpd_tags import LOOKUP_STR_FORMAT, Tag
from .scte35_enums import SpliceCommandType
from .attribute_parsers import get_int_value, get_bool_value


class SpliceInfoSection(Tag):

    @cached_property
    def procotol_version(self):
        return get_int_value(self.element.attrib.get("protocolVersion"))

    @cached_property
    def splice_insert(self):
        return self.cast_single_child("SpliceInsert", SpliceInsert)

    @cached_property
    def time_signal(self):
        return self.cast_single_child("TimeSignal", TimeSignal)

    @cached_property
    def command_type(self):
        if self.splice_insert:
            return SpliceCommandType.SPLICE_INSERT

        if self.time_signal:
            return SpliceCommandType.TIME_SIGNAL

    @cached_property
    def command(self):
        if self.command_type == SpliceCommandType.SPLICE_INSERT:
            return self.splice_insert

        if self.command_type == SpliceCommandType.TIME_SIGNAL:
            return self.time_signal


class SpliceInsert(Tag):

    @cached_property
    def splice_event_id(self):
        return get_int_value(self.element, "spliceEventId")

    @cached_property
    def splice_event_cancel_indicator(self):
        return get_bool_value(self.element.attrib.get("spliceEventCancelIndicator"))

    @cached_property
    def out_of_network_indicator(self):
        return get_bool_value(self.element.attrib.get("outOfNetworkIndicator"))

    @cached_property
    def splice_immediate_flag(self):
        return get_bool_value(self.element.attrib.get("spliceImmediateFlag"))

    @cached_property
    def unique_program_id(self):
        return get_int_value(self.element, "uniqueProgramId")

    @cached_property
    def avail_num(self):
        return get_int_value(self.element, "availNum")

    @cached_property
    def avails_expected(self):
        return get_int_value(self.element, "availsExpected")

    @cached_property
    def program(self):
        return self.cast_single_child("Program", Program)

    @cached_property
    def break_duration(self):
        return self.cast_single_child("BreakDuration", BreakDuration)


class Program(Tag):

    @cached_property
    def splice_time(self):
        return self.cast_single_child("SpliceTime", SpliceTime)


class SpliceTime(Tag):

    @cached_property
    def pts_time(self):
        return get_int_value(self.element.attrib.get("ptsTime"))


class BreakDuration(Tag):
    @cached_property
    def auto_return(self):
        return get_bool_value(self.element.attrib.get("autoReturn"))

    @cached_property
    def duration(self):
        return get_int_value(self.element.attrib.get("duration"))


class TimeSignal(Tag):

    pass


class Signal(Tag):
    @cached_property
    def binary(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="Binary"))
        return nodes[0].text if nodes else None
