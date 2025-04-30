import re
from datetime import datetime, timedelta, timezone
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from lxml import etree
from threefive3 import Cue

import mpd_inspector.namespaces as ns
import mpd_inspector.parser.mpd_tags as mpd_tags
from mpd_inspector.parser.enums import (
    AddressingMode,
    PeriodType,
    PresentationType,
    TemplateVariable,
)
from mpd_inspector.provenance import ValueProvenance
from mpd_inspector.scte35.scte35_enums import SpliceCommandType


class BaseInspector:
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._tag = None
        self._value_provenances: Dict[str, ValueProvenance] = {}

    def __getattr__(self, name):
        """Defers calls to unknown properties or methods to the tag"""
        return getattr(self._tag, name)

    def set_value_provenance(self, name: str, provenance: ValueProvenance) -> None:
        """Sets the provenance of a value."""
        self._value_provenances[name] = provenance

    def get_value_provenance(self, name: str) -> Optional[ValueProvenance]:
        """Gets the provenance of a value if it exists."""
        # First we access the property to make sure it's calculated
        getattr(self, name)

        return self._value_provenances.get(name)


class MPDInspector(BaseInspector):
    def __init__(self, mpd: mpd_tags.MPD):
        super().__init__()
        self._tag = mpd
        self._base_uri = ""

    @property
    def base_uri(self) -> str:
        return self._base_uri

    @base_uri.setter
    def base_uri(self, value: str):
        self._base_uri = value

    def is_vod(self):
        if self._tag.type == PresentationType.STATIC:
            return True
        return False

    def is_live(self):
        if self._tag.type == PresentationType.DYNAMIC:
            return True
        return False

    @cached_property
    def xpath(self):
        return "//MPD"

    @cached_property
    def periods(self):
        return [
            PeriodInspector(mpd_inspector=self, period=period)
            for period in self._tag.periods
        ]

    @cached_property
    def availability_start_time(self):
        # Calculation logic
        orig_value = self._tag.availability_start_time
        if orig_value:
            self.set_value_provenance(
                "availability_start_time", ValueProvenance.EXPLICIT
            )
            return orig_value
        else:
            self.set_value_provenance(
                "availability_start_time", ValueProvenance.DEFAULT
            )
            return datetime.fromtimestamp(0.0, tz=timezone.utc)

    @cached_property
    def full_urls(self):
        if self._tag.base_urls:
            return [
                urljoin(self.base_uri, base_url.text)
                for base_url in self._tag.base_urls
            ]
        return [self.base_uri]


class PeriodInspector(BaseInspector):
    def __init__(self, mpd_inspector: MPDInspector, period: mpd_tags.Period):
        super().__init__()
        self._mpd_inspector = mpd_inspector
        self._tag = period

    @cached_property
    def adaptation_sets(self):
        return [
            AdaptationSetInspector(period_inspector=self, adaptation_set=adaptation_set)
            for adaptation_set in self._tag.adaptation_sets
        ]

    @cached_property
    def event_streams(self):
        return [
            EventStreamInspector(period_inspector=self, event_stream=event_stream)
            for event_stream in self._tag.event_streams
        ]

    @cached_property
    def index(self) -> int:
        """Return the index of the period in the MPD"""
        return self._mpd_inspector._tag.periods.index(self._tag)

    @cached_property
    def xpath(self) -> str:
        """Return the XPath in the MPD to the period node"""
        return self._mpd_inspector.xpath + f"/Period[{self.index + 1}]"

    @cached_property
    def sequence(self) -> int:
        """Return the position of the period in the MPD Period sequence"""
        return self.index + 1

    @cached_property
    def type(self) -> PeriodType:
        if self._tag.start:
            return PeriodType.REGULAR
        else:
            if self._mpd_inspector.type == PresentationType.DYNAMIC:
                if self.index == 0 or (
                    not self._mpd_inspector._tag.periods[self.index - 1].duration
                ):
                    return PeriodType.EARLY_AVAILABLE

        if self._tag.duration and len(self._mpd_inspector._tag.periods) > (
            self.index + 1
        ):
            return PeriodType.EARLY_TERMINATED

    @cached_property
    def start_time(self) -> datetime | timedelta:
        """Returns the clock time for the start of the period, calculating it from other periods if necessary"""
        if self._tag.start is not None:
            self.set_value_provenance("start_time", ValueProvenance.EXPLICIT)
            start_offset = self._tag.start
        else:
            # TODO - implement all other possible cases
            # pure VOD (static manifest), first period starts at 0
            if self.index == 0 and self._mpd_inspector.type == PresentationType.STATIC:
                self.set_value_provenance("start_time", ValueProvenance.DEFAULT)
                start_offset = timedelta(seconds=0)

            # later periods for static and dynamic manifests
            if (
                self.index > 0
                and self._mpd_inspector._tag.periods[self.index - 1].duration
            ):
                self.set_value_provenance("start_time", ValueProvenance.DERIVED)
                start_offset = (
                    self._mpd_inspector.periods[self.index - 1].start_time
                    + self._mpd_inspector.periods[self.index - 1].duration
                )

        # For VOD manifests, return timedelta
        if self._mpd_inspector.type == PresentationType.STATIC:
            return start_offset
        # For live manifests, add to availabilityStartTime
        elif self._mpd_inspector.availability_start_time:
            # Only set the provenance to DERIVED if it wasn't already set
            if "start_time" not in self._value_provenances:
                self.set_value_provenance("start_time", ValueProvenance.DERIVED)
            return self._mpd_inspector.availability_start_time + start_offset
        else:
            return start_offset

    @cached_property
    def duration(self) -> timedelta:
        if self._tag.duration:
            self.set_value_provenance("duration", ValueProvenance.EXPLICIT)
            return self._tag.duration
        else:
            # TODO - implement all other possible cases
            #  - Last period, use the mediaPresentationDuration (for VOD), or calculate from segments
            if self.index < len(self._mpd_inspector._tag.periods) - 1:
                self.set_value_provenance("duration", ValueProvenance.DERIVED)
                return (
                    self._mpd_inspector.periods[self.index + 1].start_time
                    - self.start_time
                )
            # VOD
            if self._mpd_inspector.type == PresentationType.STATIC:
                # Single Period
                if len(self._mpd_inspector._tag.periods) == 1:
                    self.set_value_provenance("duration", ValueProvenance.DERIVED)
                    return self._mpd_inspector._tag.media_presentation_duration

    @cached_property
    def end_time(self) -> datetime:
        if self.duration:
            self.set_value_provenance("end_time", ValueProvenance.DERIVED)
            return self.start_time + self.duration
        else:
            return None

    @cached_property
    def full_urls(self):
        if not self._tag.base_urls:
            return self._mpd_inspector.full_urls
        else:
            return [
                urljoin(mpd_base_url, period_base_url.text)
                for mpd_base_url in self._mpd_inspector.full_urls
                for period_base_url in self._tag.base_urls
            ]


class AdaptationSetInspector(BaseInspector):
    def __init__(
        self, period_inspector: PeriodInspector, adaptation_set: mpd_tags.AdaptationSet
    ):
        super().__init__()
        self._period_inspector = period_inspector
        self._mpd_inspector = period_inspector._mpd_inspector
        self._tag = adaptation_set

    @cached_property
    def index(self) -> int:
        """Return the index of the period in the MPD"""
        return self._period_inspector._tag.adaptation_sets.index(self._tag)

    @cached_property
    def xpath(self) -> str:
        """Return the XPath in the MPD to the adaptation set node"""
        return self._period_inspector.xpath + f"/AdaptationSet[{self.index + 1}]"

    @cached_property
    def representations(self):
        return [
            RepresentationInspector(
                adaptation_set_inspector=self, representation=representation
            )
            for representation in self._tag.representations
        ]

    @cached_property
    def full_urls(self):
        if not self._tag.base_urls:
            return self._period_inspector.full_urls
        else:
            return [
                urljoin(period_base_url, adapt_base_url.text)
                for period_base_url in self._period_inspector.full_urls
                for adapt_base_url in self._tag.base_urls
            ]


class RepresentationInspector(BaseInspector):
    def __init__(
        self,
        adaptation_set_inspector: AdaptationSetInspector,
        representation: mpd_tags.Representation,
    ):
        super().__init__()
        self._adaptation_set_inspector = adaptation_set_inspector
        self._period_inspector = adaptation_set_inspector._period_inspector
        self._mpd_inspector = adaptation_set_inspector._mpd_inspector
        self._tag = representation

    @cached_property
    def index(self) -> int:
        """Return the index of the period in the MPD"""
        return self._adaptation_set_inspector._tag.representations.index(self._tag)

    @cached_property
    def xpath(self) -> str:
        """Return the XPath in the MPD to the representation node"""
        return (
            self._adaptation_set_inspector.xpath + f"/Representation[{self.index + 1}]"
        )

    @cached_property
    def full_urls(self):
        if not self._tag.base_urls:
            return self._adaptation_set_inspector.full_urls
        else:
            return [
                urljoin(period_base_url, repr_base_url.text)
                for period_base_url in self._period_inspector.full_urls
                for repr_base_url in self._tag.base_urls
            ]

    @cached_property
    def segment_information(self):
        """Return the element that defines the way to access the media segments.
        The term 'Segment Information' is taken from ISO/IEC 23009-1, 5.3.9.2.1"""

        return SegmentInformationInspector(self)

    @cached_property
    def width(self):
        if self._tag.width:
            self.set_value_provenance("width", ValueProvenance.EXPLICIT)
            return self._tag.width
        else:
            self.set_value_provenance("width", ValueProvenance.INHERITED)
            return self._adaptation_set_inspector.width

    @cached_property
    def height(self):
        if self._tag.height:
            self.set_value_provenance("height", ValueProvenance.EXPLICIT)
            return self._tag.height
        else:
            self.set_value_provenance("height", ValueProvenance.INHERITED)
            return self._adaptation_set_inspector.height


class SegmentInformationInspector(BaseInspector):
    def __init__(self, representation_inspector: RepresentationInspector):
        super().__init__()
        self._representation_inspector = representation_inspector
        self._adaptation_set_inspector = (
            representation_inspector._adaptation_set_inspector
        )
        self._period_inspector = representation_inspector._period_inspector
        self._mpd_inspector = representation_inspector._mpd_inspector
        self._tag = self.tag

    @cached_property
    def tag(self):
        """The MPD tag that contains the actual segment information"""
        # TODO - the DASH spec seems to allow for inheritance of properties, not just entire nodes

        # On the current node
        if self._representation_inspector.segment_template:
            self.set_value_provenance("tag", ValueProvenance.EXPLICIT)
            return self._representation_inspector.segment_template
        elif self._representation_inspector.segment_list:
            self.set_value_provenance("tag", ValueProvenance.EXPLICIT)
            return self._representation_inspector.segment_list
        elif self._representation_inspector.segment_base:
            self.set_value_provenance("tag", ValueProvenance.EXPLICIT)
            return self._representation_inspector.segment_base

        # Or on the parent adaptation set node
        if self._adaptation_set_inspector.segment_template:
            self.set_value_provenance("tag", ValueProvenance.INHERITED)
            return self._adaptation_set_inspector.segment_template
        elif self._adaptation_set_inspector.segment_list:
            self.set_value_provenance("tag", ValueProvenance.INHERITED)
            return self._adaptation_set_inspector.segment_list
        elif self._adaptation_set_inspector.segment_base:
            self.set_value_provenance("tag", ValueProvenance.INHERITED)
            return self._adaptation_set_inspector.segment_base

        # or even on the period node
        if self._period_inspector.segment_template:
            self.set_value_provenance("tag", ValueProvenance.INHERITED)
            return self._period_inspector.segment_template
        elif self._period_inspector.segment_list:
            self.set_value_provenance("tag", ValueProvenance.INHERITED)
            return self._period_inspector.segment_list
        elif self._period_inspector.segment_base:
            self.set_value_provenance("tag", ValueProvenance.INHERITED)
            return self._period_inspector.segment_base

    @cached_property
    def addressing_mode(self):
        if isinstance(self.tag, mpd_tags.SegmentBase):
            return AddressingMode.INDEXED
        if (
            isinstance(self.tag, mpd_tags.SegmentTemplate)
            and not self.tag.segment_timeline
        ):
            return AddressingMode.SIMPLE
        if isinstance(self.tag, mpd_tags.SegmentTemplate) and self.tag.segment_timeline:
            return AddressingMode.EXPLICIT

    @cached_property
    def addressing_template(self):
        if self.addressing_mode in [AddressingMode.EXPLICIT, AddressingMode.SIMPLE]:
            if "$Time" in self.tag.media:
                return TemplateVariable.TIME
            if "$Number" in self.tag.media:
                return TemplateVariable.NUMBER

    def full_urls(self, attribute_name, replacements: dict = {}):
        all_replacements = {
            "$RepresentationID": self._representation_inspector.id,
            "$Bandwidth": self._representation_inspector.bandwidth,
        }
        all_replacements.update(replacements)

        media_url = getattr(self.tag, attribute_name)
        full_urls = []
        if media_url:
            for representation_url in self._representation_inspector.full_urls:
                full_url = representation_url + media_url
                full_url = url_placeholder_replacer(full_url, all_replacements)
                full_urls.append(full_url)

        return full_urls

    @cached_property
    def segments(self) -> List["MediaSegment"]:
        """Return a list of all media segments"""
        if (
            self.addressing_mode == AddressingMode.SIMPLE
            and self.addressing_template == TemplateVariable.NUMBER
        ):
            return list(self._generate_segments_from_simple_number_addressing())

        elif (
            self.addressing_mode == AddressingMode.EXPLICIT
            and self.addressing_template == TemplateVariable.TIME
        ):
            return list(self._generate_segments_from_explicit_time_addressing())

        elif (
            self.addressing_mode == AddressingMode.EXPLICIT
            and self.addressing_template == TemplateVariable.NUMBER
        ):
            return list(self._generate_segments_from_explicit_number_addressing())

        else:
            raise NotImplementedError("This addressing mode has not been implemented")

    def _generate_segments_from_simple_number_addressing(self):
        segment_number = self.tag.start_number
        segment_duration = self.tag.duration / self.tag.timescale
        total_duration_so_far = 0
        while total_duration_so_far < self._period_inspector.duration.total_seconds():
            total_duration_so_far += segment_duration
            yield MediaSegment(
                number=segment_number,
                duration=segment_duration,
                urls=self.full_urls("media", {"$Number": segment_number}),
                init_urls=self.full_urls("initialization", {}),
                duration_cumulative=total_duration_so_far,
            )
            segment_number += 1

    def _generate_segments_from_explicit_time_addressing(self):
        timescale = self.tag.timescale
        segment_start = None
        this_segment = None
        for segment in self.tag.segment_timeline.segments:
            if segment.t is not None:
                segment_start = segment.t

            this_segment = self._generate_media_segment(
                start=segment_start,
                duration=segment.d,
                timescale=timescale,
                previous_segment=this_segment,
            )
            segment_start += segment.d
            yield this_segment

            if segment.r:
                for r in range(segment.r):
                    this_segment = self._generate_media_segment(
                        start=segment_start,
                        duration=segment.d,
                        timescale=timescale,
                        previous_segment=this_segment,
                    )
                    segment_start += segment.d
                    yield this_segment

    def _generate_segments_from_explicit_number_addressing(self):
        timescale = self.tag.timescale
        segment_start = None
        segment_number = self.start_number
        this_segment = None
        for segment in self.tag.segment_timeline.segments:
            if segment.t is not None:
                segment_start = segment.t

            this_segment = self._generate_media_segment(
                start=segment_start,
                duration=segment.d,
                timescale=timescale,
                number=segment_number,
                previous_segment=this_segment,
            )
            segment_start += segment.d
            segment_number += 1
            yield this_segment

            if segment.r:
                for r in range(segment.r):
                    this_segment = self._generate_media_segment(
                        start=segment_start,
                        duration=segment.d,
                        timescale=timescale,
                        number=segment_number,
                        previous_segment=this_segment,
                    )
                    segment_number += 1
                    segment_start += segment.d
                    yield this_segment

    def _generate_media_segment(
        self, start, duration, timescale, number=None, previous_segment=None
    ):
        # The segment start time in the MPD timeline is determined by the delta
        # between S@t and the SegmentTemplate@presentationTimeOffset (which corresponds to the Period start time)
        segment_start_time = self._period_inspector.start_time + timedelta(
            seconds=(start - (self.tag.presentation_time_offset or 0)) / timescale
        )
        duration_in_s = duration / timescale
        cumul_duration = duration_in_s
        if previous_segment:
            cumul_duration += previous_segment.duration_cumulative

        return MediaSegment(
            start_time=segment_start_time,
            duration=duration_in_s,
            number=number,
            time=start,
            urls=self.full_urls("media", {"$Number": number, "$Time": start}),
            init_urls=self.full_urls("initialization", {}),
            duration_cumulative=cumul_duration,
        )


class MediaSegment:
    def __init__(
        self,
        urls: List[str],
        duration: float,
        init_urls: List[str] = [],
        number: Optional[int] = None,
        time: Optional[int] = None,
        start_time: Optional[datetime | float] = None,
        duration_cumulative: Optional[
            float
        ] = None,  # cumulative duration of all segments in the period up to and including this segment
    ):
        self.urls = urls
        self.init_urls = init_urls
        self.duration = duration
        self.number = number
        self.time = time
        if isinstance(start_time, float):
            self.start_time = datetime.fromtimestamp(start_time)
        else:
            self.start_time = start_time
        self.duration_cumulative = duration_cumulative

    def __repr__(self):
        return f"MediaSegment({self.urls})"

    @cached_property
    def end_time(self):
        if self.start_time:
            return self.start_time + timedelta(seconds=self.duration)


class EventStreamInspector(BaseInspector):
    def __init__(
        self, period_inspector: PeriodInspector, event_stream: mpd_tags.EventStream
    ):
        self._period_inspector = period_inspector
        self._tag = event_stream

    @cached_property
    def events(self):
        evs = []
        for event in self._tag.events:
            if self.scheme_id_uri == "urn:scte:scte35:2013:xml":
                evs.append(Scte35XmlEventInspector(self, event))
            elif self.scheme_id_uri == "urn:scte:scte35:2014:xml+bin":
                evs.append(Scte35BinaryEventInspector(self, event))
            else:
                evs.append(EventInspector(self, event))
        return evs


class EventInspector(BaseInspector):
    def __init__(
        self, event_stream_inspector: EventStreamInspector, event: mpd_tags.Event
    ):
        self._event_stream_inspector = event_stream_inspector
        self._tag = event

    @cached_property
    def content(self):
        return self._tag.content

    @cached_property
    def relative_presentation_time(self):
        """Presentation time relative to the period start"""
        relative_offset = self._tag.presentation_time or 0
        presentation_time_offset = (
            self._event_stream_inspector._tag.presentation_time_offset or 0
        )
        timescale = self._event_stream_inspector._tag.timescale

        return timedelta(seconds=relative_offset / timescale) - timedelta(
            seconds=presentation_time_offset / timescale
        )

    @cached_property
    def presentation_time(self):
        period_start_time = self._event_stream_inspector._period_inspector.start_time
        return period_start_time + self.relative_presentation_time

    @cached_property
    def duration(self):
        if self._tag.duration:
            return timedelta(
                seconds=self._tag.duration / self._event_stream_inspector._tag.timescale
            )


class Scte35EventInspector(EventInspector):
    pass


class Scte35BinaryEventInspector(Scte35EventInspector):
    @cached_property
    def command_type(self):
        return SpliceCommandType(self.content.command.command_type)

    @cached_property
    def content(self):
        # According to DASH-IF IOP v4.3 10.15.3, The Event should contain only 1 element (apparently)
        # return Scte35Parser.from_element(self._tag.content[0])
        element = self._tag.content[0]

        # force the namespace to be the standard one
        change_namespace(element, ns.SCTE35_NAMESPACE)

        return Cue(self._get_payload(element))

    def _get_payload(self, element: etree._Element):
        return element.findall(f"{{{ns.SCTE35_NAMESPACE}}}Binary")[0].text


class Scte35XmlEventInspector(Scte35EventInspector):
    @cached_property
    def content(self):
        """Return the parsed SpliceInfoSection from the event content"""
        from mpd_inspector.scte35 import SCTE35Parser

        return SCTE35Parser.from_event_tag(self._tag)

    @cached_property
    def command_type(self):
        """Return the command type from the parsed SpliceInfoSection"""
        if self.content.splice_insert is not None:
            return SpliceCommandType.SPLICE_INSERT
        elif self.content.time_signal is not None:
            return SpliceCommandType.TIME_SIGNAL
        elif self.content.splice_null is not None:
            return SpliceCommandType.SPLICE_NULL
        elif self.content.bandwidth_reservation is not None:
            return SpliceCommandType.BANDWIDTH_RESERVATION
        elif self.content.private_command is not None:
            return SpliceCommandType.PRIVATE
        elif self.content.splice_schedule is not None:
            return SpliceCommandType.SPLICE_SCHEDULE
        else:
            return None


def change_namespace(element, new_namespace):
    # Function to change namespace recursively

    # Update the tag of the current element
    if "}" in element.tag:
        # Remove the old namespace and keep the local name
        local_name = element.tag.split("}", 1)[1]
    else:
        local_name = element.tag
    element.tag = f"{{{new_namespace}}}{local_name}"

    # Recursively update children
    for child in element:
        change_namespace(child, new_namespace)


def url_placeholder_replacer(url, values):
    # Function to replace placeholders with values, allowing for optional formatter strings like $Number%05d$
    def replacer(match):
        var = match.group(1)
        fmt = match.group(2)
        val = values.get(var, var)
        return (fmt % val) if fmt else str(val)

    pattern = r"(\$[A-Za-z0-9_]+)(%[^$]+)?\$"
    result = re.sub(pattern, replacer, url)
    return result
