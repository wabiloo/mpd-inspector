from functools import cached_property
from typing import Optional

from ..mpd_parser.enums import (
    PresentationType,
    PeriodType,
    AddressingMode,
    TemplateVariable,
)
import src.mpd_parser.tags as tags
from .value_statements import ExplicitValue, DefaultValue, ImplicitValue, InheritedValue
from datetime import timedelta, datetime


class MPDInspector:
    def __init__(self, mpd: tags.MPD):
        self._mpd = mpd
        self._enhance()

    def _enhance(self):
        # self._mpd.is_vod = self.is_vod()
        # self._mpd.is_live = self.is_live()
        for period in self._mpd.periods:
            PeriodInspector(self._mpd, period)

    def __getattr__(self, name):
        return getattr(self._mpd, name)

    def is_vod(self):
        if self._mpd.type == PresentationType.STATIC:
            return True
        return False

    def is_live(self):
        if self._mpd.type == PresentationType.DYNAMIC:
            return True
        return False

    @cached_property
    def xpath(self):
        return "//MPD"

    @cached_property
    def periods(self):
        return [
            PeriodInspector(mpd_inspector=self, period=period)
            for period in self._mpd.periods
        ]

    @cached_property
    def availability_start_time(self):
        # Calculation logic
        orig_value = self._mpd.availability_start_time
        if orig_value:
            return ExplicitValue(orig_value)
        else:
            return DefaultValue(datetime.datetime.fromtimestamp(0.0))


class PeriodInspector:
    def __init__(self, mpd_inspector: MPDInspector, period: tags.Period):
        self._mpd_inspector = mpd_inspector
        self._period = period
        self._enhance()

    def _enhance(self):
        pass

    def __getattr__(self, name):
        return getattr(self._period, name)

    @cached_property
    def adaptation_sets(self):
        return [
            AdaptationSetInspector(period_inspector=self, adaptation_set=adaptation_set)
            for adaptation_set in self._period.adaptation_sets
        ]

    @cached_property
    def index(self) -> int:
        """Return the index of the period in the MPD"""
        return self._mpd_inspector._mpd.periods.index(self._period)

    @cached_property
    def xpath(self) -> str:
        """Return the XPath in the MPD to the period node"""
        return self._mpd_inspector.xpath + f"/Period[{self.index+1}]"

    @cached_property
    def sequence(self) -> int:
        """Return the position of the period in the MPD Period sequence"""
        return self.index + 1

    @cached_property
    def type(self) -> PeriodType:
        if self._period.start:
            return PeriodType.REGULAR
        else:
            if self._mpd_inspector.type == PresentationType.DYNAMIC:
                if self.index == 0 or (
                    not self._mpd_inspector._mpd.periods[self.index - 1].duration
                ):
                    return PeriodType.EARLY_AVAILABLE

        if self._period.duration and len(self._mpd_inspector._mpd.periods) > (
            self.index + 1
        ):
            return PeriodType.EARLY_TERMINATED

    @cached_property
    def start_time(self) -> datetime:
        """Returns the clock time for the start of the period, calculating it from other periods if necessary"""
        if self._period.start:
            start_offset = self._period.start
        else:
            # TODO - implement all other possible cases
            if (
                self.index > 0
                and self._mpd_inspector._mpd.periods[self.index - 1].duration
            ):
                start_offset = (
                    self._mpd_inspector.periods[self.index - 1].start_time
                    + self._mpd_inspector.periods[self.index - 1].duration
                )
            if self.index == 0 and self._mpd_inspector.type == PresentationType.STATIC:
                return DefaultValue(0)

        # Add it to the availabilityStartTime
        if self._mpd_inspector.availability_start_time:
            return ImplicitValue(
                self._mpd_inspector.availability_start_time + start_offset
            )

    @cached_property
    def duration(self) -> timedelta:
        if self._period.duration:
            return ExplicitValue(self._period.duration)
        else:
            # TODO - implement all other possible cases
            #  - Last period, use the mediaPresentationDuration (for VOD), or calculate from segments
            if self.index < len(self._mpd_inspector._mpd.periods) - 1:
                return ImplicitValue(
                    self._mpd_inspector.periods[self.index + 1].start_time
                    - self.start_time
                )
            # VOD
            if self._mpd_inspector.type == PresentationType.STATIC:
                # Single Period
                if len(self._mpd_inspector._mpd.periods) == 1:
                    return ImplicitValue(
                        self._mpd_inspector._mpd.media_presentation_duration
                    )


class AdaptationSetInspector:
    def __init__(
        self, period_inspector: PeriodInspector, adaptation_set: tags.AdaptationSet
    ):
        self._period_inspector = period_inspector
        self._mpd_inspector = period_inspector._mpd_inspector
        self._adaptation_set = adaptation_set
        self._enhance()

    def _enhance(self):
        pass

    def __getattr__(self, name):
        return getattr(self._adaptation_set, name)

    @cached_property
    def index(self) -> int:
        """Return the index of the period in the MPD"""
        return self._period_inspector._period.adaptation_sets.index(
            self._adaptation_set
        )

    @cached_property
    def xpath(self) -> str:
        """Return the XPath in the MPD to the adaptation set node"""
        return self._period_inspector.xpath + f"/AdaptationSet[{self.index+1}]"

    @cached_property
    def representations(self):
        return [
            RepresentationInspector(
                adaptation_set_inspector=self, representation=representation
            )
            for representation in self._adaptation_set.representations
        ]


class RepresentationInspector:
    def __init__(
        self,
        adaptation_set_inspector: AdaptationSetInspector,
        representation: tags.Representation,
    ):
        self._adaptation_set_inspector = adaptation_set_inspector
        self._period_inspector = adaptation_set_inspector._period_inspector
        self._mpd_inspector = adaptation_set_inspector._mpd_inspector
        self._representation = representation
        self._enhance()

    def _enhance(self):
        pass

    def __getattr__(self, name):
        return getattr(self._representation, name)

    @cached_property
    def index(self) -> int:
        """Return the index of the period in the MPD"""
        return self._adaptation_set_inspector._adaptation_set.representations.index(
            self._representation
        )

    @cached_property
    def xpath(self) -> str:
        """Return the XPath in the MPD to the representation node"""
        return self._adaptation_set_inspector.xpath + f"/Representation[{self.index+1}]"

    @cached_property
    def segment_information(self):
        """Return the element that defines the way to access the media segments"""
        return SegmentInformationInspector(self)


class SegmentInformationInspector:
    def __init__(self, representation_inspector: RepresentationInspector):
        self._representation_inspector = representation_inspector
        self._adaptation_set_inspector = (
            representation_inspector._adaptation_set_inspector
        )
        self._period_inspector = representation_inspector._period_inspector
        self._mpd_inspector = representation_inspector._mpd_inspector
        self._enhance()

    def _enhance(self):
        pass

    def __getattr__(self, name):
        # any unknown attr, we send to the original segment definition
        return getattr(self.info, name)

    @cached_property
    def info(self):
        # TODO - the DASH spec seems to allow for inheritance of properties, not just entire nodes

        # On the current node
        if self._representation_inspector.segment_template:
            return ExplicitValue(self._representation_inspector.segment_template)
        elif self._representation_inspector.segment_list:
            return ExplicitValue(self._representation_inspector.segment_list)
        elif self._representation_inspector.segment_base:
            return ExplicitValue(self._representation_inspector.segment_base)

        # Or on the parent adaptation set node
        if self._adaptation_set_inspector.segment_template:
            return InheritedValue(self._adaptation_set_inspector.segment_template)
        elif self._adaptation_set_inspector.segment_list:
            return InheritedValue(self._adaptation_set_inspector.segment_list)
        elif self._adaptation_set_inspector.segment_base:
            return InheritedValue(self._adaptation_set_inspector.segment_base)

        # or even on the period node
        if self._period_inspector.segment_template:
            return InheritedValue(self._period_inspector.segment_template)
        elif self._period_inspector.segment_list:
            return InheritedValue(self._period_inspector.segment_list)
        elif self._period_inspector.segment_base:
            return InheritedValue(self._period_inspector.segment_base)

    @cached_property
    def addressing_mode(self):
        if isinstance(self.info.value, tags.SegmentBase):
            return AddressingMode.INDEXED
        if (
            isinstance(self.info.value, tags.SegmentTemplate)
            and not self.info.segment_timeline
        ):
            return AddressingMode.SIMPLE
        if (
            isinstance(self.info.value, tags.SegmentTemplate)
            and self.info.segment_timeline
        ):
            return AddressingMode.EXPLICIT

    @cached_property
    def addressing_template(self):
        if self.addressing_mode in [AddressingMode.EXPLICIT, AddressingMode.SIMPLE]:
            if "$Time$" in self.info.value.media:
                return TemplateVariable.TIME
            if "$Number$" in self.info.value.media:
                return TemplateVariable.NUMBER

    def resolve_url(self, attribute_name, replacements: dict):

        all_replacements = {"$RepresentationID$": self._representation_inspector.id}
        all_replacements.update(replacements)

        media_url = getattr(self.info.value, attribute_name)
        if media_url:
            for var, value in all_replacements.items():
                media_url = media_url.replace(var, str(value))

        return media_url

    @cached_property
    def segments(self):
        if (
            self.addressing_mode == AddressingMode.SIMPLE
            and self.addressing_template == TemplateVariable.NUMBER
        ):
            segment_number = self.info.value.start_number
            segment_duration = self.info.value.duration / self.info.value.timescale
            total_duration_so_far = 0
            while (
                total_duration_so_far < self._period_inspector.duration.total_seconds()
            ):
                yield MediaSegment(
                    number=segment_number,
                    duration=segment_duration,
                    url=self.resolve_url("media", {"$Number$": segment_number}),
                    init_url=self.resolve_url("initialization", {}),
                )
                segment_number += 1
                total_duration_so_far += segment_duration

        elif (
            self.addressing_mode == AddressingMode.EXPLICIT
            and self.addressing_template == TemplateVariable.TIME
        ):
            timescale = self.info.value.timescale
            segment: tags.Segment
            segment_start = None
            for segment in self.info.segment_timeline.segments:
                if segment.t:
                    segment_start = segment.t

                yield MediaSegment(
                    start=segment_start / timescale,
                    duration=segment.d / timescale,
                    url=self.resolve_url("media", {"$Time$": segment_start}),
                    init_url=self.resolve_url("initialization", {}),
                )
                segment_start += segment.d
                if segment.r:
                    for r in range(segment.r):
                        yield MediaSegment(
                            start=segment_start / timescale,
                            duration=segment.d / timescale,
                            url=self.resolve_url("media", {"$Time$": segment_start}),
                            init_url=self.resolve_url("initialization", {}),
                        )
                        segment_start += segment.d

        # elif self.addressing_mode == AddressingMode.EXPLICIT:
        #     return [
        #         SegmentInspector(self, segment)
        #         for segment in self.info.segment_timeline.segments
        #     ]
        else:
            raise NotImplementedError("This addressing mode has not been implemented")


class SegmentInspector:
    def __init__(
        self,
        segment_information_inspector: SegmentInformationInspector,
        segment: tags.Segment,
    ):
        self._segment_information_inspector = segment_information_inspector
        self._segment = segment
        self._enhance()

    def _enhance(self):
        pass

    def __getattr__(self, name):
        return getattr(self._segment, name)


class MediaSegment:
    def __init__(
        self,
        url: str,
        duration: float,
        init_url: Optional[str] = None,
        number: Optional[int] = None,
        start: Optional[datetime | float] = None,
    ):
        self.url = url
        self.init_url = init_url
        self.duration = duration
        self.number = number
        if isinstance(start, float):
            start = timedelta(seconds=start)
        else:
            self.start = start

    def __repr__(self):
        return f"MediaSegment({self.url})"

    @cached_property
    def end(self):
        if self.start:
            return self.start + timedelta(seconds=self.duration)
