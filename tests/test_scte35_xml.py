"""Tests for SCTE35 XML parsing"""

import pytest
from lxml import etree

from mpd_inspector.parser.exceptions import UnknownElementTreeParseError
from mpd_inspector.parser.mpd_tags import Event
from mpd_inspector.scte35 import SCTE35Parser, SpliceInfoSection


def test_parse_splice_insert():
    """Test parsing a SCTE35 XML with SpliceInsert"""
    xml = """
    <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864" tier="4095">
      <scte35:SpliceInsert spliceEventId="15" spliceEventCancelIndicator="false" outOfNetworkIndicator="true" spliceImmediateFlag="false" uniqueProgramId="1" availNum="18" availsExpected="255">
        <scte35:Program>
          <scte35:SpliceTime ptsTime="584648676"/>
        </scte35:Program>
        <scte35:BreakDuration autoReturn="false" duration="7956395"/>
      </scte35:SpliceInsert>
    </scte35:SpliceInfoSection>
    """
    scte35 = SCTE35Parser.from_string(xml)

    assert isinstance(scte35, SpliceInfoSection)
    assert scte35.protocol_version == 0
    assert scte35.pts_adjustment == 7769619864
    assert scte35.tier == 4095

    assert scte35.splice_insert is not None
    assert scte35.splice_insert.splice_event_id == 15
    assert scte35.splice_insert.splice_event_cancel_indicator is False
    assert scte35.splice_insert.out_of_network_indicator is True
    assert scte35.splice_insert.splice_immediate_flag is False
    assert scte35.splice_insert.unique_program_id == 1
    assert scte35.splice_insert.avail_num == 18
    assert scte35.splice_insert.avails_expected == 255

    assert scte35.splice_insert.program is not None
    assert scte35.splice_insert.program.splice_time is not None
    assert scte35.splice_insert.program.splice_time.pts_time == 584648676

    assert scte35.splice_insert.break_duration is not None
    assert scte35.splice_insert.break_duration["auto_return"] is False
    assert scte35.splice_insert.break_duration["duration"] == 7956395


def test_parse_time_signal_with_namespaced_attributes():
    """Test parsing a SCTE35 XML with TimeSignal using namespaced attributes"""
    xml = """
    <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" scte35:ptsAdjustment="7431158430">
      <scte35:TimeSignal>
        <scte35:SpliceTime scte35:ptsTime="4308089774"/>
      </scte35:TimeSignal>
      <scte35:SegmentationDescriptor scte35:segmentationEventId="44240" scte35:segmentationEventCancelIndicator="false" scte35:segmentationDuration="2739039" scte35:segmentationTypeId="48" scte35:segmentNum="0" scte35:segmentsExpected="0">
        <scte35:SegmentationUpid scte35:segmentationUpidType="12" scte35:segmentationUpidFormat="hexbinary">42454C4C7B2261223A33302E34332C2270223A22312F37222C2269223A223132323433303933352F37383132333630222C2262223A2230303A30323A33323B3034222C2263223A2254534E31222C2274223A317D</scte35:SegmentationUpid>
      </scte35:SegmentationDescriptor>
    </scte35:SpliceInfoSection>
    """
    scte35 = SCTE35Parser.from_string(xml)

    assert isinstance(scte35, SpliceInfoSection)
    assert scte35.pts_adjustment == 7431158430

    assert scte35.time_signal is not None
    assert scte35.time_signal.splice_time is not None
    assert scte35.time_signal.splice_time.pts_time == 4308089774

    assert len(scte35.segmentation_descriptors) == 1
    descriptor = scte35.segmentation_descriptors[0]
    assert descriptor.segmentation_event_id == 44240
    assert descriptor.segmentation_event_cancel_indicator is False
    assert descriptor.segmentation_duration == 2739039
    assert descriptor.segmentation_type_id == 48
    assert descriptor.segment_num == 0
    assert descriptor.segments_expected == 0

    assert descriptor.segmentation_upid is not None
    assert descriptor.segmentation_upid.segmentation_upid_type == 12
    assert descriptor.segmentation_upid.segmentation_upid_format == "hexbinary"
    assert (
        descriptor.segmentation_upid.text
        == "42454C4C7B2261223A33302E34332C2270223A22312F37222C2269223A223132323433303933352F37383132333630222C2262223A2230303A30323A33323B3034222C2263223A2254534E31222C2274223A317D"
    )


def test_parse_time_signal_without_namespaced_attributes():
    """Test parsing a SCTE35 XML with TimeSignal using non-namespaced attributes"""
    xml = """
    <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" ptsAdjustment="7431158430">
      <scte35:TimeSignal>
        <scte35:SpliceTime ptsTime="4308089774"/>
      </scte35:TimeSignal>
      <scte35:SegmentationDescriptor segmentationEventId="44240" segmentationEventCancelIndicator="false" segmentationDuration="2739039" segmentationTypeId="48" segmentNum="0" segmentsExpected="0">
        <scte35:SegmentationUpid segmentationUpidType="12" segmentationUpidFormat="hexbinary">42454C4C7B2261223A33302E34332C2270223A22312F37222C2269223A223132323433303933352F37383132333630222C2262223A2230303A30323A33323B3034222C2263223A2254534E31222C2274223A317D</scte35:SegmentationUpid>
      </scte35:SegmentationDescriptor>
    </scte35:SpliceInfoSection>
    """
    scte35 = SCTE35Parser.from_string(xml)

    assert isinstance(scte35, SpliceInfoSection)
    assert scte35.pts_adjustment == 7431158430

    assert scte35.time_signal is not None
    assert scte35.time_signal.splice_time is not None
    assert scte35.time_signal.splice_time.pts_time == 4308089774

    assert len(scte35.segmentation_descriptors) == 1
    descriptor = scte35.segmentation_descriptors[0]
    assert descriptor.segmentation_event_id == 44240
    assert descriptor.segmentation_event_cancel_indicator is False
    assert descriptor.segmentation_duration == 2739039
    assert descriptor.segmentation_type_id == 48
    assert descriptor.segment_num == 0
    assert descriptor.segments_expected == 0

    assert descriptor.segmentation_upid is not None
    assert descriptor.segmentation_upid.segmentation_upid_type == 12
    assert descriptor.segmentation_upid.segmentation_upid_format == "hexbinary"
    assert (
        descriptor.segmentation_upid.text
        == "42454C4C7B2261223A33302E34332C2270223A22312F37222C2269223A223132323433303933352F37383132333630222C2262223A2230303A30323A33323B3034222C2263223A2254534E31222C2274223A317D"
    )


def test_parse_with_ext():
    """Test parsing a SCTE35 XML with Ext element"""
    xml = """
    <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016">
      <scte35:TimeSignal>
        <scte35:SpliceTime/>
      </scte35:TimeSignal>
      <scte35:SegmentationDescriptor segmentationTypeId="48">
        <scte35:SegmentationUpid segmentationUpidType="12" segmentationUpidFormat="hexbinary">42454C4C7B2261223A33302E34332C2270223A22312F37222C2269223A223132323433303933352F37383132333630222C2262223A2230303A30323A33323B3034222C2263223A2254534E31222C2274223A317D</scte35:SegmentationUpid>
      </scte35:SegmentationDescriptor>
      <scte35:Ext availType="48" timeFromSignal="PT28.028S"/>
    </scte35:SpliceInfoSection>    
    """
    scte35 = SCTE35Parser.from_string(xml)

    assert scte35.ext is not None
    assert scte35.ext.avail_type == 48
    assert scte35.ext.time_from_signal == "PT28.028S"


def test_parse_with_different_namespace():
    """Test parsing a SCTE35 XML with a different namespace"""
    xml = """
    <scte35:SpliceInfoSection xmlns:scte35="http://example.com/scte35" protocolVersion="0" ptsAdjustment="7769619864" tier="4095">
      <scte35:SpliceInsert spliceEventId="15" spliceEventCancelIndicator="false" outOfNetworkIndicator="true" spliceImmediateFlag="false" uniqueProgramId="1" availNum="18" availsExpected="255">
        <scte35:Program>
          <scte35:SpliceTime ptsTime="584648676"/>
        </scte35:Program>
        <scte35:BreakDuration autoReturn="false" duration="7956395"/>
      </scte35:SpliceInsert>
    </scte35:SpliceInfoSection>
    """
    scte35 = SCTE35Parser.from_string(xml)

    assert isinstance(scte35, SpliceInfoSection)
    assert scte35.protocol_version == 0
    assert scte35.pts_adjustment == 7769619864
    assert scte35.tier == 4095

    assert scte35.splice_insert is not None
    assert scte35.splice_insert.splice_event_id == 15
    assert scte35.splice_insert.splice_event_cancel_indicator is False
    assert scte35.splice_insert.out_of_network_indicator is True
    assert scte35.splice_insert.splice_immediate_flag is False
    assert scte35.splice_insert.unique_program_id == 1
    assert scte35.splice_insert.avail_num == 18
    assert scte35.splice_insert.avails_expected == 255


def test_invalid_xml():
    """Test parsing invalid XML"""
    with pytest.raises(Exception):
        SCTE35Parser.from_string("invalid xml")


def test_to_string():
    """Test converting SCTE35 object back to string"""
    xml = """
    <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864" tier="4095">
      <scte35:SpliceInsert spliceEventId="15" spliceEventCancelIndicator="false" outOfNetworkIndicator="true" spliceImmediateFlag="false" uniqueProgramId="1" availNum="18" availsExpected="255">
        <scte35:Program>
          <scte35:SpliceTime ptsTime="584648676"/>
        </scte35:Program>
        <scte35:BreakDuration autoReturn="false" duration="7956395"/>
      </scte35:SpliceInsert>
    </scte35:SpliceInfoSection>
    """
    scte35 = SCTE35Parser.from_string(xml)
    output = SCTE35Parser.to_string(scte35)

    # Parse the output back to verify it's valid XML
    SCTE35Parser.from_string(output)


def test_from_dash_event_simple():
    """Test extracting SpliceInfoSection from a simple DASH event"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin">
        <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864" tier="4095">
            <scte35:SpliceInsert spliceEventId="15" spliceEventCancelIndicator="false" outOfNetworkIndicator="true"/>
        </scte35:SpliceInfoSection>
    </Event>
    """
    event = etree.fromstring(event_xml)
    scte35 = SCTE35Parser.from_dash_event(event)

    assert isinstance(scte35, SpliceInfoSection)
    assert scte35.protocol_version == 0
    assert scte35.pts_adjustment == 7769619864
    assert scte35.tier == 4095
    assert scte35.splice_insert is not None
    assert scte35.splice_insert.splice_event_id == 15
    assert scte35.splice_insert.splice_event_cancel_indicator is False
    assert scte35.splice_insert.out_of_network_indicator is True


def test_from_dash_event_nested():
    """Test that nested SpliceInfoSection is not found in DASH event"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin">
        <SomeWrapper>
            <AnotherWrapper>
                <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864">
                    <scte35:TimeSignal>
                        <scte35:SpliceTime ptsTime="584648676"/>
                    </scte35:TimeSignal>
                </scte35:SpliceInfoSection>
            </AnotherWrapper>
        </SomeWrapper>
    </Event>
    """
    event = etree.fromstring(event_xml)

    with pytest.raises(UnknownElementTreeParseError) as exc_info:
        SCTE35Parser.from_dash_event(event)
    assert "No SpliceInfoSection found as direct child of DASH event" in str(
        exc_info.value
    )


def test_from_dash_event_multiple():
    """Test that first direct child SpliceInfoSection is returned when multiple exist"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin">
        <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864">
            <scte35:TimeSignal>
                <scte35:SpliceTime ptsTime="584648676"/>
            </scte35:TimeSignal>
        </scte35:SpliceInfoSection>
        <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="1" ptsAdjustment="1234567890">
            <scte35:SpliceInsert spliceEventId="15"/>
        </scte35:SpliceInfoSection>
    </Event>
    """
    event = etree.fromstring(event_xml)
    scte35 = SCTE35Parser.from_dash_event(event)

    assert isinstance(scte35, SpliceInfoSection)
    assert scte35.protocol_version == 0
    assert scte35.pts_adjustment == 7769619864
    assert scte35.time_signal is not None
    assert scte35.time_signal.splice_time is not None
    assert scte35.time_signal.splice_time.pts_time == 584648676


def test_from_dash_event_no_splice_info():
    """Test handling DASH event with no SpliceInfoSection"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin">
        <SomeOtherElement>Content</SomeOtherElement>
    </Event>
    """
    event = etree.fromstring(event_xml)

    with pytest.raises(UnknownElementTreeParseError) as exc_info:
        SCTE35Parser.from_dash_event(event)
    assert "No SpliceInfoSection found as direct child of DASH event" in str(
        exc_info.value
    )


def test_from_event_tag_simple():
    """Test extracting SpliceInfoSection from a simple Event tag"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin">
        <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864" tier="4095">
            <scte35:SpliceInsert spliceEventId="15" spliceEventCancelIndicator="false" outOfNetworkIndicator="true"/>
        </scte35:SpliceInfoSection>
    </Event>
    """
    event_element = etree.fromstring(event_xml)
    event = Event(event_element)
    scte35 = SCTE35Parser.from_event_tag(event)

    assert isinstance(scte35, SpliceInfoSection)
    assert scte35.protocol_version == 0
    assert scte35.pts_adjustment == 7769619864
    assert scte35.tier == 4095
    assert scte35.splice_insert is not None
    assert scte35.splice_insert.splice_event_id == 15
    assert scte35.splice_insert.splice_event_cancel_indicator is False
    assert scte35.splice_insert.out_of_network_indicator is True


def test_from_event_tag_nested():
    """Test that nested SpliceInfoSection is not found in Event tag"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin">
        <SomeWrapper>
            <AnotherWrapper>
                <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864">
                    <scte35:TimeSignal>
                        <scte35:SpliceTime ptsTime="584648676"/>
                    </scte35:TimeSignal>
                </scte35:SpliceInfoSection>
            </AnotherWrapper>
        </SomeWrapper>
    </Event>
    """
    event_element = etree.fromstring(event_xml)
    event = Event(event_element)

    with pytest.raises(UnknownElementTreeParseError) as exc_info:
        SCTE35Parser.from_event_tag(event)
    assert "No SpliceInfoSection found as direct child of DASH event" in str(
        exc_info.value
    )


def test_from_event_tag_multiple():
    """Test that first direct child SpliceInfoSection is returned when multiple exist"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin">
        <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="0" ptsAdjustment="7769619864">
            <scte35:TimeSignal>
                <scte35:SpliceTime ptsTime="584648676"/>
            </scte35:TimeSignal>
        </scte35:SpliceInfoSection>
        <scte35:SpliceInfoSection xmlns:scte35="http://www.scte.org/schemas/35/2016" protocolVersion="1" ptsAdjustment="1234567890">
            <scte35:SpliceInsert spliceEventId="15"/>
        </scte35:SpliceInfoSection>
    </Event>
    """
    event_element = etree.fromstring(event_xml)
    event = Event(event_element)
    scte35 = SCTE35Parser.from_event_tag(event)

    assert isinstance(scte35, SpliceInfoSection)
    assert scte35.protocol_version == 0
    assert scte35.pts_adjustment == 7769619864
    assert scte35.time_signal is not None
    assert scte35.time_signal.splice_time is not None
    assert scte35.time_signal.splice_time.pts_time == 584648676


def test_from_event_tag_no_splice_info():
    """Test handling Event tag with no SpliceInfoSection"""
    event_xml = """
    <Event xmlns="urn:mpeg:dash:event:2012" schemeIdUri="urn:scte:scte35:2014:xml+bin">
        <SomeOtherElement>Content</SomeOtherElement>
    </Event>
    """
    event_element = etree.fromstring(event_xml)
    event = Event(event_element)

    with pytest.raises(UnknownElementTreeParseError) as exc_info:
        SCTE35Parser.from_event_tag(event)
    assert "No SpliceInfoSection found as direct child of DASH event" in str(
        exc_info.value
    )
