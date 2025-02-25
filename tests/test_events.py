"""
Test the inspection of full manifests with events
"""

from datetime import timedelta
from pytest import mark
from mpd_inspector.parser.parser import MPDParser
from mpd_inspector.inspector import (
    MPDInspector,
    Scte35BinaryEventInspector,
    Scte35XmlEventInspector,
)
from lxml.etree import _Element

from mpd_inspector.parser.scte35_enums import SpliceCommandType
from threefive3 import Cue


@mark.parametrize(
    "input_file",
    [
        "./manifests/live-mediapackage-scte35-singleperiod.mpd",
    ],
)
def test_find_events_in_live_mpd(input_file):
    mpd = MPDParser.from_file(input_file)

    inspector = MPDInspector(mpd)

    for i, period in enumerate(inspector.periods):
        # testing the tags themselves
        assert len(period._tag.event_streams) == 1
        assert period._tag.event_streams[0].scheme_id_uri == "urn:scte:scte35:2013:xml"
        assert len(period._tag.event_streams[0].events) == 1
        assert period._tag.event_streams[0].events[0].duration == 7956395

        cont = period._tag.event_streams[0].events[0].content
        assert len(cont) == 1
        assert isinstance(cont[0], _Element)

        # testing the inspector
        assert len(period.event_streams) == 1
        assert len(period.event_streams[0].events) == 1
        event0 = period.event_streams[0].events[0]
        assert isinstance(event0, Scte35XmlEventInspector)
        assert event0.duration == timedelta(seconds=88.40438889)

        cont = event0.content
        assert isinstance(cont, Cue)

        assert event0.command_type == SpliceCommandType.SPLICE_INSERT
        # assert cont.command_type == SpliceCommandType.SPLICE_INSERT
        # assert isinstance(cont.splice_insert, scte35_tags.SpliceInsert)
        # assert isinstance(cont.command, scte35_tags.SpliceInsert)
        # assert cont.command.program.splice_time.pts_time == 584648676


@mark.parametrize(
    "input_file",
    [
        "./manifests/vspp-live-multiperiod-events-scte35bin.mpd",
    ],
)
def test_binary_scte35_events_in_live_mpd(input_file):
    mpd = MPDParser.from_file(input_file)
    inspector = MPDInspector(mpd)

    period1 = inspector.periods[1]
    assert len(period1.event_streams) == 1
    assert len(period1.event_streams[0].events) == 2

    event0 = period1.event_streams[0].events[0]
    assert event0.presentation_time == period1.start_time
    assert isinstance(event0, Scte35BinaryEventInspector)
    assert isinstance(event0.content, Cue)
    assert event0.command_type == SpliceCommandType.TIME_SIGNAL
