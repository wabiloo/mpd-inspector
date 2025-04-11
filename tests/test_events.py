"""Tests for event parsing"""

from datetime import timedelta

import pytest
from lxml import etree
from lxml.etree import _Element
from pytest import mark
from threefive3 import Cue

from mpd_inspector.inspector import (
    EventStreamInspector,
    MPDInspector,
    PeriodInspector,
    Scte35BinaryEventInspector,
    Scte35XmlEventInspector,
)
from mpd_inspector.parser.mpd_tags import Event, EventStream
from mpd_inspector.parser.parser import MPDParser
from mpd_inspector.scte35 import SpliceInfoSection
from mpd_inspector.scte35.scte35_enums import SpliceCommandType


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
        assert isinstance(cont, SpliceInfoSection)

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


def test_scte35_xml_event():
    """Test SCTE35 XML event parsing"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin" presentationTime="0" duration="0" id="1">
        <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864" tier="4095">
            <scte35:SpliceInsert spliceEventId="15" spliceEventCancelIndicator="false" outOfNetworkIndicator="true"/>
        </scte35:SpliceInfoSection>
    </Event>
    """
    event_element = etree.fromstring(event_xml)
    event = Event(event_element)
    event_stream = EventStream(event_element)
    event_stream_inspector = EventStreamInspector(
        PeriodInspector(None, None), event_stream
    )
    event_inspector = Scte35XmlEventInspector(event_stream_inspector, event)

    # Test content returns a parsed SpliceInfoSection
    content = event_inspector.content
    assert isinstance(content, SpliceInfoSection)
    assert content.protocol_version == 0
    assert content.pts_adjustment == 7769619864
    assert content.tier == 4095
    assert content.splice_insert is not None
    assert content.splice_insert.splice_event_id == 15
    assert content.splice_insert.splice_event_cancel_indicator is False
    assert content.splice_insert.out_of_network_indicator is True

    # Test command_type still works
    assert event_inspector.command_type == SpliceCommandType.SPLICE_INSERT
