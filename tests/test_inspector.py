"""
Test the inspection of full manifests
"""

from datetime import datetime, timedelta, timezone
import isodate
from pytest import mark
from src.mpd_parser.parser import Parser
from src.mpd_inspector.inspector import (
    AdaptationSetInspector,
    MPDInspector,
    PeriodInspector,
    RepresentationInspector,
)
from src.mpd_inspector.value_statements import (
    ExplicitValue,
    ImplicitValue,
    InheritedValue,
)
from src.mpd_parser.enums import PresentationType, AddressingMode


@mark.parametrize(
    "input_file",
    [
        "./manifests/bitmovin-sample.mpd",
    ],
)
def test_inspect_vod_file(input_file):
    mpd = Parser.from_file(input_file)
    assert mpd.id == "f08e80da-bf1d-4e3d-8899-f0f6155f6efa"

    inspector = MPDInspector(mpd)

    assert inspector.id == mpd.id
    assert inspector.is_vod() is True

    period0 = inspector.periods[0]
    assert isinstance(period0, PeriodInspector)
    assert period0.sequence == 1

    adapset0 = period0.adaptation_sets[0]
    assert isinstance(adapset0, AdaptationSetInspector)
    assert len(adapset0.representations) == 6

    repr0 = adapset0.representations[0]
    assert isinstance(repr0, RepresentationInspector)
    assert repr0.id == "180_250000"
    assert repr0.xpath == "//MPD/Period[1]/AdaptationSet[1]/Representation[1]"


@mark.parametrize(
    "input_file",
    [
        "./manifests/live-mediapackage-scte35-singleperiod.mpd",
    ],
)
def test_inspect_live_manifest(input_file):
    mpd = Parser.from_file(input_file)
    inspector = MPDInspector(mpd)
    assert inspector.type == PresentationType.DYNAMIC
    assert inspector.is_live() is True
    assert inspector.id == mpd.id
    assert isinstance(inspector.availability_start_time, ExplicitValue)
    assert inspector.availability_start_time == isodate.parse_datetime(
        "2023-04-11T21:23:16.18Z"
    )


@mark.parametrize(
    "input_file",
    [
        "./manifests/broadpeakio-ssai-multiperiod.mpd",
    ],
)
def test_inspect_live_manifest_multiperiod(input_file):
    mpd = Parser.from_file(input_file)
    inspector = MPDInspector(mpd)
    assert inspector.id == mpd.id
    assert inspector.unparsed_attr("availabilityStartTime") == "1970-01-01T00:00:00Z"
    assert isinstance(inspector.availability_start_time, ExplicitValue)
    assert inspector.availability_start_time == datetime.fromtimestamp(
        0, tz=timezone.utc
    )
    assert len(inspector.periods) == 3

    assert inspector.periods[0].index == 0
    assert inspector.periods[0].sequence == 1
    assert inspector.periods[0].start_time == datetime.fromisoformat(
        "2024-08-05 12:19:29.74700Z"
    )
    assert isinstance(inspector.periods[0].duration, ImplicitValue)
    assert inspector.periods[0].duration.value == timedelta(seconds=181.917)

    assert inspector.periods[1].sequence == 2
    assert inspector.periods[1].start_time == datetime.fromisoformat(
        "2024-08-05 12:22:31.66400Z"
    )
