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
            first_segment_starts=[
                datetime.fromisoformat("2024-08-05T12:21:44.330333Z"),
                datetime.fromisoformat("2024-08-05T12:21:44.339000Z"),
            ],
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

        for j, adapset in enumerate(period.adaptation_sets):
            for rep in adapset.representations:
                # slightly optimistic case as segments align with period start
                segments = list(rep.segment_information.segments)
                if expected_periods[i].get("first_segment_starts"):
                    assert (
                        segments[0].start_time
                        == expected_periods[i]["first_segment_starts"][j]
                    )
                else:
                    assert segments[0].start_time == expected_periods[i]["start"]
