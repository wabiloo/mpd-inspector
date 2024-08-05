# mpd-inspector

## Overview
This is a module to parse MPEG-DASH Media Presentation Documents (aka. MPD) from files or URLs, and interpret them
This package is built as a fork from the excellent [mpd-parser](https://github.com/avishaycohen/mpd-parser/tree/main). The main reasons for forking it are:
1. I needed to change the behaviour to be closer to the MPEG-DASH spec, in particular DASH-IF IOP rules.
1. I wanted to parse all MPD attributes into native Python types (including for datetimes and durations)
2. I wanted to be able to expose unparsed elements
3. I wanted to add a layer of inspection/analysis to make it possible to calculate implicit/derived values (eg. start and duration of periods in multi-period MPD) - in particular again for validation against the DASH-IF Interoperability guidance


## Installation
```shell
$ python -m pip install mpd-inspector
```

## Usage
### Importing

```python
from mpd_parser.parser import Parser
```
### parse from string
```python
with open("path/to/file.mpd", mode="r") as manifest_file:
    mpd_string = manifest_file.read()
    parsed_mpd = Parser.from_string(mpd_string)
```

### parse from file
```python
input_file = "path/to/file.mpd"
mpd = Parser.from_file(input_file)
```

### parse from url
```python
input_url = "https://my-server.com/path/to/stream.mpd"
mpd = Parser.from_url(input_url)
```

### inspect it
```python
mpd_inspector = MPDInspector(mpd)
```

### convert back to string
```python
mpd_as_xml_string = Parser.to_string(parsed_mpd)
```

## Example manifests
Taken from a variety of places

### Build locally
```shell
poetry build
```
