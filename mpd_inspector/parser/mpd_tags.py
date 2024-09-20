# pylint: disable=missing-function-docstring

"""
The tags module holds all the type of different nodes
you may come across when parsing MPD manifest file.
"""
from functools import cached_property
from typing import Optional, Any

from lxml.etree import Element

from .enums import PresentationType
from .attribute_parsers import (
    organize_ns,
    get_float_value,
    get_bool_value,
    get_int_value,
    get_list_of_type,
    get_datetime_value,
    get_duration_value,
)

LOOKUP_STR_FORMAT = './*[local-name(.) = "{target}"]'
KEYS_NOT_FOR_SETTING = ["element", "tag_map", "encoding"]


class Tag:
    """Generic repr of mpd tag object"""

    def __init__(self, element: Element) -> None:
        self.element: Element = element
        self.tag_map: dict = {}

    def __setattr__(self, key: str, value: Any) -> None:
        """overload default setattr to make changes to the lxml element when attributes are changed by user"""
        super().__setattr__(key, value)
        # attributes that are not generated by lxml parsing
        if key in KEYS_NOT_FOR_SETTING:
            return

        # not an attribute, but part of the element
        if key == "text":
            self.element.text = value
            return

        # most attributes have a camel case name in DASH
        element_attrib_name = self.to_camel_case(key)

        # and those that don't, are mapped in tag_map
        if self.tag_map and key in self.tag_map:
            element_attrib_name = self.tag_map.get(key, element_attrib_name)

        # the value is None, remove attribute
        if not value:
            self.element.attrib.pop(element_attrib_name, None)
            return

        # list value should turn to a comma separated string
        if isinstance(value, list):
            self.element.attrib[element_attrib_name] = ",".join(map(str, value))
            return

        self.element.attrib[element_attrib_name] = str(value)

    @classmethod
    def to_camel_case(cls, snake_case_string: str) -> str:
        """convert snake_case to lowerCamelCase"""
        lead, *follow = snake_case_string.split("_")
        return "".join([lead, *map(str.capitalize, follow)])

    def unparsed_attr(self, key: str) -> Optional[str]:
        """get unparsed attribute value"""
        return self.element.attrib.get(key)

    def cast_single_child(self, node_name, class_name):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target=node_name))
        return class_name(nodes[0]) if nodes else None


class TextTag(Tag):
    """A tag that uses the text member frequently"""

    @cached_property
    def text(self) -> str:
        return self.element.text


class PSSH(Tag):
    """PSSH tag class"""

    @cached_property
    def pssh(self):
        return self.element.attrib.get("pssh")


class ContentProtection(Tag):
    """Tag for content protection"""

    def __init__(self, element):
        super().__init__(element)
        self.tag_map = {
            "default_key_id": "default_KId",
            "ns2_key_id": "ns2:default_KID",
            "cenc_default_kid": "cenc:default_KID",
        }

    @cached_property
    def scheme_id_uri(self):
        return self.element.attrib.get("schemeIdUri")

    @cached_property
    def value(self):
        return self.element.attrib.get("value")

    @cached_property
    def id(self):
        return self.element.attrib.get("id")

    @cached_property
    def default_key_id(self):
        return self.element.attrib.get("default_KId")

    @cached_property
    def ns2_key_id(self):
        return self.element.attrib.get("ns2:default_KID")

    @cached_property
    def cenc_default_kid(self):
        return self.element.attrib.get("cenc:default_KID")

    @cached_property
    def pssh(self):
        return PSSH(self.element.attrib.get("cenc:pssh"))


class RepresentationBase(Tag):  # pylint: disable=too-many-public-methods
    """Generic representation tag"""

    def __init__(self, element):
        super().__init__(element)
        self.tag_map = {
            "maximum_sap_period": "maximumSAPPeriod",
            "start_with_sap": "startWithSAP",
        }

    @cached_property
    def profile(self):
        return self.element.attrib.get("profile")

    @cached_property
    def profiles(self):
        return self.element.attrib.get("profiles")

    @cached_property
    def width(self):
        return get_int_value(self.element.attrib.get("width"))

    @cached_property
    def height(self):
        return get_int_value(self.element.attrib.get("height"))

    @cached_property
    def sar(self):
        return self.element.attrib.get("sar")

    @cached_property
    def frame_rate(self):
        return self.element.attrib.get("frameRate")

    @cached_property
    def audio_sampling_rate(self):
        return self.element.attrib.get("audioSamplingRate")

    @cached_property
    def mime_type(self):
        return self.element.attrib.get("mimeType")

    @cached_property
    def segment_profiles(self):
        return self.element.attrib.get("segmentProfiles")

    @cached_property
    def codecs(self):
        return self.element.attrib.get("codecs")

    @cached_property
    def maximum_sap_period(self):
        return get_float_value(self.element.attrib.get("maximumSAPPeriod"))

    @cached_property
    def start_with_sap(self):
        return get_int_value(self.element.attrib.get("startWithSAP"))

    @cached_property
    def max_playout_rate(self):
        return get_float_value(self.element.attrib.get("maxPlayoutRate"))

    @cached_property
    def coding_dependency(self):
        return get_bool_value(self.element.attrib.get("codingDependency"))

    @cached_property
    def scan_type(self):
        return self.element.attrib.get("scanType")

    @cached_property
    def frame_packings(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="FramePacking")
            )
        ]

    @cached_property
    def audio_channel_configurations(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="AudioChannelConfiguration")
            )
        ]

    @cached_property
    def content_protections(self):
        return [
            ContentProtection(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="ContentProtection")
            )
        ]

    @cached_property
    def essential_properties(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="EssentialProperty")
            )
        ]

    @cached_property
    def supplemental_properties(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SupplementalProperty")
            )
        ]

    @cached_property
    def inband_event_stream(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="InbandEventStream")
            )
        ]


class ContentComponent(Tag):
    """Content Compoenet tag representation"""

    @cached_property
    def id(self):
        return get_int_value(self.element.attrib.get("id"))

    @cached_property
    def lang(self):
        return self.element.attrib.get("lang")

    @cached_property
    def content_type(self):
        return self.element.attrib.get("contentType")

    @cached_property
    def par(self):
        return self.element.attrib.get("par")

    @cached_property
    def accessibilities(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Accessibility")
            )
        ]

    @cached_property
    def roles(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Role"))
        ]

    @cached_property
    def ratings(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Rating"))
        ]

    @cached_property
    def viewpoints(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Viewpoint")
            )
        ]


class SubRepresentation(RepresentationBase):
    """A sub representation tag"""

    @cached_property
    def level(self):
        return get_int_value(self.element.attrib.get("level"))

    @cached_property
    def bandwidth(self):
        return get_int_value(self.element.attrib.get("bandwidth"))

    @cached_property
    def dependency_level(self):
        return get_list_of_type(int, self.element.attrib.get("dependencyLevel"))

    @cached_property
    def content_component(self):
        return get_list_of_type(str, self.element.attrib.get("contentComponent"))


class Representation(RepresentationBase):
    """Representation tag"""

    @cached_property
    def id(self):
        return self.element.attrib.get("id")

    @cached_property
    def bandwidth(self):
        return get_int_value(self.element.attrib.get("bandwidth"))

    @cached_property
    def quality_ranking(self):
        return get_int_value(self.element.attrib.get("qualityRanking"))

    @cached_property
    def dependency_id(self):
        return get_list_of_type(str, self.element.attrib.get("dependencyId"))

    @cached_property
    def num_channels(self):
        return get_int_value(self.element.attrib.get("numChannels"))

    @cached_property
    def sample_rate(self):
        return get_int_value(self.element.attrib.get("sampleRate"))

    @cached_property
    def base_urls(self):
        return [
            BaseURL(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="BaseURL"))
        ]

    @cached_property
    def segment_base(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentBase"))
        return SegmentBase(nodes[0]) if nodes else None

    @cached_property
    def segment_list(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentList"))
        return SegmentList(nodes[0]) if nodes else None

    @cached_property
    def segment_template(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentTemplate"))
        return SegmentTemplate(nodes[0]) if nodes else None

    @cached_property
    def sub_representations(self):
        return [
            SubRepresentation(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SubRepresentation")
            )
        ]


class AdaptationSet(RepresentationBase):  # pylint: disable=too-many-public-methods
    """Adaptation Set tag representation"""

    def __init__(self, element):
        super().__init__(element)
        self.tag_map = {"subsegment_starts_with_sap": "subsegmentStartsWithSAP"}

    @cached_property
    def id(self):
        return get_int_value(self.element.attrib.get("id"))

    @cached_property
    def group(self):
        return get_int_value(self.element.attrib.get("group"))

    @cached_property
    def lang(self):
        return self.element.attrib.get("lang")

    @cached_property
    def label(self):
        return self.element.attrib.get("label")

    @cached_property
    def content_type(self):
        return self.element.attrib.get("contentType")

    @cached_property
    def par(self):
        return self.element.attrib.get("par")

    @cached_property
    def min_bandwidth(self):
        return get_int_value(self.element.attrib.get("minBandwidth"))

    @cached_property
    def max_bandwidth(self):
        return get_int_value(self.element.attrib.get("maxBandwidth"))

    @cached_property
    def min_width(self):
        return get_int_value(self.element.attrib.get("minWidth"))

    @cached_property
    def max_width(self):
        return get_int_value(self.element.attrib.get("maxWidth"))

    @cached_property
    def min_height(self):
        return get_int_value(self.element.attrib.get("minHeight"))

    @cached_property
    def max_height(self):
        return get_int_value(self.element.attrib.get("maxHeight"))

    @cached_property
    def min_frame_rate(self):
        return self.element.attrib.get("minFrameRate")

    @cached_property
    def max_frame_rate(self):
        return self.element.attrib.get("maxFrameRate")

    @cached_property
    def segment_alignment(self):
        return get_bool_value(self.element.attrib.get("segmentAlignment"))

    @cached_property
    def selection_priority(self):
        return get_int_value(self.element.attrib.get("selectionPriority"))

    @cached_property
    def subsegment_starts_with_sap(self):
        return get_int_value(self.element.attrib.get("subsegmentStartsWithSAP"))

    @cached_property
    def subsegment_alignment(self):
        return get_bool_value(self.element.attrib.get("subsegmentAlignment"))

    @cached_property
    def bitstream_switching(self):
        return get_bool_value(self.element.attrib.get("bitstreamSwitching"))

    @cached_property
    def accessibilities(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Accessibility")
            )
        ]

    @cached_property
    def roles(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Role"))
        ]

    @cached_property
    def ratings(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Rating"))
        ]

    @cached_property
    def viewpoints(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Viewpoint")
            )
        ]

    @cached_property
    def content_components(self):
        return [
            ContentComponent(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="ContentComponent")
            )
        ]

    @cached_property
    def base_urls(self):
        return [
            BaseURL(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="BaseURL"))
        ]

    @cached_property
    def segment_base(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentBase"))
        return SegmentBase(nodes[0]) if nodes else None

    @cached_property
    def segment_list(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentList"))
        return SegmentList(nodes[0]) if nodes else None

    @cached_property
    def segment_template(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentTemplate"))
        return SegmentTemplate(nodes[0]) if nodes else None

    @cached_property
    def representations(self):
        return [
            Representation(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Representation")
            )
        ]


class S(Tag):
    """S tag representation. A single segment of video"""

    @cached_property
    def t(self):
        return get_int_value(self.element.attrib.get("t"))

    @cached_property
    def d(self):
        return get_int_value(self.element.attrib.get("d"))

    @cached_property
    def r(self):
        return get_int_value(self.element.attrib.get("r"))


class Title(TextTag):
    """Title tag representation"""


class Source(TextTag):
    """Source tag representation"""


class Location(TextTag):
    """Location tag representation"""


class Copyright(TextTag):
    """Copyright tag representation"""


class ProgramInfo(Tag):
    """Program information tag representation"""

    def __init__(self, element):
        super().__init__(element)
        self.tag_map = {"more_info_url": "moreInformationURL"}

    @cached_property
    def lang(self):
        return self.element.attrib.get("lang")

    @cached_property
    def more_info_url(self):
        return self.element.attrib.get("moreInformationURL")

    @cached_property
    def titles(self):
        return [
            Title(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Title"))
        ]

    @cached_property
    def sources(self):
        return [
            Source(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Source"))
        ]

    @cached_property
    def copy_rights(self):
        return [
            Copyright(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Copyright")
            )
        ]


class BaseURL(Tag):
    """Base URL tag representation"""

    @cached_property
    def text(self) -> str:
        return self.element.text

    @cached_property
    def service_location(self) -> str:
        return self.element.attrib.get("serviceLocation")

    @cached_property
    def byte_range(self) -> str:
        return self.element.attrib.get("byteRange")

    @cached_property
    def availability_time_offset(self) -> float:
        return get_float_value(self.element.attrib.get("availabilityTimeOffset"))

    @cached_property
    def availability_time_complete(self) -> Optional[bool]:
        return get_bool_value(self.element.attrib.get("availabilityTimeComplete"))


class Descriptor(Tag):
    """Reusable class for tag that have url, id and a value"""

    @cached_property
    def scheme_id_uri(self) -> str:
        return self.element.attrib.get("schemeIdUri")

    @cached_property
    def id(self) -> str:
        return self.element.attrib.get("id")

    @cached_property
    def value(self) -> str:
        return self.element.attrib.get("value")


class UTCTiming(Descriptor):
    """UTC Timing information tag representation"""


class AssetIdentifiers(Descriptor):
    """Asset Identifier tag"""


class SegmentTimeline(Tag):
    """SegmentTimeline tag repr"""

    @cached_property
    def segments(self):
        return [
            S(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="S"))
        ]


class MultipleSegmentBaseInformationMixin:
    """Multiple segments tag"""

    @cached_property
    def timescale(self):
        return get_int_value(self.element.attrib.get("timescale"))

    @cached_property
    def duration(self):
        return get_int_value(self.element.attrib.get("duration"))

    @cached_property
    def start_number(self):
        return get_int_value(self.element.attrib.get("startNumber"))

    @cached_property
    def presentation_time_offset(self):
        return get_int_value(self.element.attrib.get("presentationTimeOffset"))

    @cached_property
    def availability_time_offset(self):
        return get_float_value(self.element.attrib.get("availabilityTimeOffset"))

    @cached_property
    def availability_time_complete(self):
        return get_bool_value(self.element.attrib.get("availabilityTimeComplete"))

    @cached_property
    def initialization(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="Initialization"))
        return Initialization(nodes[0]) if nodes else None

    @cached_property
    def segment_timeline(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentTimeline"))
        return SegmentTimeline(nodes[0]) if nodes else None

    @cached_property
    def bitstream_switching(self):
        nodes = self.element.xpath(
            LOOKUP_STR_FORMAT.format(target="BitstreamSwitching")
        )
        return BitstreamSwitching(nodes[0]) if nodes else None


class SegmentBase(Tag, MultipleSegmentBaseInformationMixin):
    """Basic Segment tag representation"""

    @cached_property
    def index_range(self):
        return self.element.attrib.get("indexRange")

    @cached_property
    def index_range_exact(self):
        return get_bool_value(self.element.attrib.get("indexRangeExact"))

    @cached_property
    def representation_index(self):
        nodes = self.element.xpath(
            LOOKUP_STR_FORMAT.format(target="RepresentationIndex")
        )
        return RepresentationIndex(nodes[0]) if nodes else None


class SegmentURL(Tag):
    """SegmentURL tag"""

    @cached_property
    def media(self):
        return self.element.attrib.get("media")

    @cached_property
    def media_range(self):
        return self.element.attrib.get("mediaRange")

    @cached_property
    def index(self):
        return self.element.attrib.get("index")

    @cached_property
    def index_range(self):
        return self.element.attrib.get("indexRange")


class SegmentList(Tag, MultipleSegmentBaseInformationMixin):
    """SegmentList tag"""

    @cached_property
    def segment_urls(self):
        return [
            SegmentURL(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentURL")
            )
        ]


class SegmentTemplate(Tag, MultipleSegmentBaseInformationMixin):

    @cached_property
    def media(self):
        return self.element.attrib.get("media")

    @cached_property
    def index(self):
        return self.element.attrib.get("index")

    @cached_property
    def initialization(self):
        return self.element.attrib.get("initialization")

    @cached_property
    def bitstream_switching(self):
        return self.element.attrib.get("bitstreamSwitching")


class Event(TextTag):
    """Single event tag"""

    @cached_property
    def message_data(self):
        return self.element.attrib.get("messageData")

    @cached_property
    def presentation_time(self):
        return get_int_value(self.element.attrib.get("presentationTime"))

    @cached_property
    def duration(self):
        return get_int_value(self.element.attrib.get("duration"))

    @cached_property
    def id(self):
        return get_int_value(self.element.attrib.get("id"))

    @cached_property
    def content(self):
        return list(self.element)


class EventStream(Descriptor):
    """Event Stream tag"""

    @cached_property
    def timescale(self):
        return get_int_value(self.element.attrib.get("timescale"))

    @cached_property
    def presentation_time_offset(self):
        return get_int_value(self.element.attrib.get("presentationTimeOffset"))

    @cached_property
    def events(self):
        return [
            Event(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Event"))
        ]


class Subset(Tag):
    """Subset tag"""

    @cached_property
    def id(self):
        return self.element.attrib.get("id")

    @cached_property
    def contains(self):
        return get_list_of_type(int, self.element.attrib.get("contains"))


class Period(Tag):
    """Period class, represents a period tag in mpd manifest."""

    @cached_property
    def id(self):
        return self.element.attrib.get("id")

    @cached_property
    def start(self):
        return get_duration_value(self.element.attrib.get("start"))

    @cached_property
    def duration(self):
        return get_duration_value(self.element.attrib.get("duration"))

    @cached_property
    def bitstream_switching(self):
        return get_bool_value(self.element.attrib.get("bitstreamSwitching"))

    @cached_property
    def base_urls(self):
        return [
            BaseURL(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="BaseURL"))
        ]

    @cached_property
    def segment_base(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentBase"))
        return SegmentBase(nodes[0]) if nodes else None

    @cached_property
    def segment_list(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentList"))
        return SegmentList(nodes[0]) if nodes else None

    @cached_property
    def segment_template(self):
        nodes = self.element.xpath(LOOKUP_STR_FORMAT.format(target="SegmentTemplate"))
        return SegmentTemplate(nodes[0]) if nodes else None

    @cached_property
    def asset_identifiers(self):
        return [
            AssetIdentifiers(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="AssetIdentifiers")
            )
        ]

    @cached_property
    def event_streams(self):
        return [
            EventStream(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="EventStream")
            )
        ]

    @cached_property
    def adaptation_sets(self):
        return [
            AdaptationSet(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="AdaptationSet")
            )
        ]

    @cached_property
    def subsets(self):
        return [
            Subset(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Subset"))
        ]


class URL(Tag):
    """Represent tags that have source-url and range attributes"""

    def __init__(self, element):
        super().__init__(element)
        self.tag_map = {"source_url": "sourceURL"}

    @cached_property
    def source_url(self):
        return self.element.attrib.get("sourceURL")

    @cached_property
    def range(self):
        return self.element.attrib.get("range")


class Initialization(URL):
    """Initialization tag representation"""


class RepresentationIndex(URL):
    """Representation Index tag representation"""


class BitstreamSwitching(URL):
    """BitstreamSwitching tag representation"""


class MPD(Tag):  # pylint: disable=too-many-public-methods
    """
        MPD class represents the root of a mpd manifest,
    it is the top most tag of an XML file following the DASH format

    the element passed for MPD should be the root of the lxml.etree
    """

    def __init__(self, element: Element, encoding: str = "utf-8"):
        super().__init__(element=element)
        self.encoding = encoding
        self.tag_map = {"cenc": "xlmns:cenc"}

    @cached_property
    def namespace(self):
        value = self.element.nsmap
        if None in self.element.nsmap.keys():
            # can't use None as key in xpath
            value = organize_ns(self.element.nsmap)
        return value

    @cached_property
    def xmlns(self):
        return self.element.nsmap.get(None)

    @cached_property
    def id(self):
        return self.element.attrib.get("id")

    @cached_property
    def type(self):
        return PresentationType(self.element.attrib.get("type"))

    @cached_property
    def profiles(self):
        return self.element.attrib.get("profiles")

    @cached_property
    def cenc(self):
        return self.element.attrib.get("xlmns:cenc")

    @cached_property
    def availability_start_time(self):
        return get_datetime_value(self.element.attrib.get("availabilityStartTime"))

    @cached_property
    def availability_end_time(self):
        return get_datetime_value(self.element.attrib.get("availabilityEndTime"))

    @cached_property
    def publish_time(self):
        return get_datetime_value(self.element.attrib.get("publishTime"))

    @cached_property
    def media_presentation_duration(self):
        return get_duration_value(self.element.attrib.get("mediaPresentationDuration"))

    @cached_property
    def minimum_update_period(self):
        return get_duration_value(self.element.attrib.get("minimumUpdatePeriod"))

    @cached_property
    def min_buffer_time(self):
        return get_duration_value(self.element.attrib.get("minBufferTime"))

    @cached_property
    def time_shift_buffer_depth(self):
        return get_duration_value(self.element.attrib.get("timeShiftBufferDepth"))

    @cached_property
    def suggested_presentation_delay(self):
        return get_duration_value(self.element.attrib.get("suggestedPresentationDelay"))

    @cached_property
    def max_segment_duration(self):
        return get_duration_value(self.element.attrib.get("maxSegmentDuration"))

    @cached_property
    def max_subsegment_duration(self):
        return get_duration_value(self.element.attrib.get("maxSubsegmentDuration"))

    @cached_property
    def program_informations(self):
        return [
            ProgramInfo(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="ProgramInformation")
            )
        ]

    @cached_property
    def base_urls(self):
        return [
            BaseURL(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="BaseURL"))
        ]

    @cached_property
    def locations(self):
        return [
            Location(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Location")
            )
        ]

    @cached_property
    def utc_timings(self):
        return [
            UTCTiming(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="UTCTiming")
            )
        ]

    @cached_property
    def periods(self):
        return [
            Period(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Period"))
        ]
