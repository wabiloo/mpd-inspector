"""
SCTE35 XML parsing module
"""

from .parser import SCTE35Parser
from .scte35_tags import (
    Ext,
    SegmentationDescriptor,
    SegmentationUpid,
    SpliceInfoSection,
    SpliceInsert,
    SpliceTime,
    TimeSignal,
)

__all__ = [
    "SCTE35Parser",
    "SpliceInfoSection",
    "SpliceInsert",
    "TimeSignal",
    "SpliceTime",
    "SegmentationDescriptor",
    "SegmentationUpid",
    "Ext",
]
