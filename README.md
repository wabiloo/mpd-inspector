# mpd-inspector

Python module to parse MPEG-DASH Media Presentation Documents (aka. MPD) from files or URLs, and inspect them. With support for SCTE35 events (binary and/or XML).

## Overview

The library provides two main components: the `MPDParser` and the `MPDInspector`. The `MPDParser` is responsible for parsing the MPD XML content (from a file, URL, or string) into a structured Python object model, converting attributes into native Python types where appropriate. It is meant to be a one-to-one mapping of the content of the MPD file to the object model. 

The `MPDInspector` takes a parsed MPD object and provides a higher-level interface for analysis and interpretation. It calculates implicit and derived values (such as segment URLs based on templates, or accurate start/end times for periods), determines provenance for values, and offers helper methods for common tasks like checking if a presentation is live or on-demand.

### Origin

This package was initially built as a fork from the excellent [mpd-parser](https://github.com/avishaycohen/mpd-parser/tree/main). The main reasons for forking it are:
1. I needed to change the behaviour to be closer to the MPEG-DASH spec, in particular DASH-IF IOP rules.
2. I wanted to parse all MPD attributes into native Python types (including for datetimes and durations)
3. I wanted to be able to expose unparsed elements
4. I wanted to add a layer of inspection/analysis to make it possible to calculate implicit/derived values (eg. start and duration of periods in multi-period MPD) - in particular again for validation against the DASH-IF Interoperability guidance
5. I wanted to add support for SCTE35 Events (both as binary and XML)

## Installation
```shell
$ python -m pip install mpd-inspector
```

## Usage
### Parsing a MPD manifest

```python
from mpd_inspector import MPDParser, MPDInspector
```
#### from string
```python
with open("path/to/file.mpd", mode="r") as manifest_file:
    mpd_string = manifest_file.read()
    parsed_mpd = MPDParser.from_string(mpd_string)
```

#### from file
```python
input_file = "path/to/file.mpd"
mpd = MPDParser.from_file(input_file)
```

#### from url
```python
input_url = "https://my-server.com/path/to/stream.mpd"
mpd = MPDParser.from_url(input_url)
```

### Inspecting the MPD manifest
Once you have a parsed MPD object (`mpd`), you can create an inspector:

```python
inspector = MPDInspector(mpd)

# Check basic MPD properties
print(f"MPD ID: {inspector.id}")
print(f"Type: {'Live' if inspector.is_live() else 'VOD'}")
if inspector.is_live():
    print(f"Availability Start Time: {inspector.availability_start_time}")
else:
    print(f"Media Presentation Duration: {inspector.media_presentation_duration}")

# Iterate through Periods
for period in inspector.periods:
    print(f"  Period {period.sequence} Start: {period.start_time}, Duration: {period.duration}")
    print(f"    Duration Provenance: {period.get_value_provenance('duration')}") # EXPLICIT, DERIVED, DEFAULT

    # Iterate through Adaptation Sets (Video, Audio, etc.)
    for adap_set in period.adaptation_sets:
        print(f"    Adaptation Set MIME Type: {adap_set.mime_type}")

        # Iterate through Representations (different bitrates/resolutions)
        for representation in adap_set.representations:
            print(f"      Representation ID: {representation.id}, Bandwidth: {representation.bandwidth}")

            # Get segment information
            segment_info = representation.segment_information
            print(f"        Segment Addressing Mode: {segment_info.addressing_mode}") # e.g., SIMPLE, EXPLICIT

            # Get segment URLs (using a generator)
            # Note: For large manifests, avoid converting the generator to a list immediately
            segment_generator = segment_info.segments
            try:
                first_segment = next(segment_generator)
                print(f"        First Segment URL(s): {first_segment.urls}")
                print(f"        First Segment Start Time: {first_segment.start_time}")
                print(f"        First Segment Duration: {first_segment.duration}")
            except StopIteration:
                print("        No segments found for this representation.")
```

For more examples, I would suggest looking at the tests.

## Example manifests
There are a variety of example manifests in the `manifests` directory, coming from a variety of sources.

