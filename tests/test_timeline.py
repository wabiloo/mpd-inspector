"""
Test the inspection of full manifests
"""

from datetime import datetime, timedelta
from pytest import mark
from mpd_inspector.parser.parser import MPDParser
from mpd_inspector.inspector import (
    MPDInspector,
)


@mark.parametrize(
    "input_file",
    [
        "./manifests/broadpeakio-ssai-multiperiod.mpd",
    ],
)
def test_inspect_vod_file(input_file):
    mpd = MPDParser.from_file(input_file)

    inspector = MPDInspector(mpd)

    expected_periods = [
        dict(
            start=datetime.fromisoformat("2024-08-05T12:19:29.74700Z"),
            end=datetime.fromisoformat("2024-08-05T12:22:31.66400Z"),
            duration=timedelta(minutes=3, seconds=1.917),
        ),
        dict(
            start=datetime.fromisoformat("2024-08-05T12:22:31.66400Z"),
            end=datetime.fromisoformat("2024-08-05T12:22:37.74400Z"),
            duration=timedelta(seconds=6.080),
        ),
        dict(
            start=datetime.fromisoformat("2024-08-05T12:22:37.74400Z"),
            end=None,
            duration=None,
        ),
    ]

    for i, period in enumerate(inspector.periods):
        assert period.start_time == expected_periods[i]["start"]
        assert period.end_time == expected_periods[i]["end"]
        assert period.duration == expected_periods[i]["duration"]
