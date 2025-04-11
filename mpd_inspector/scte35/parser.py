"""
SCTE35 XML parser module
"""

from typing import TYPE_CHECKING

from lxml import etree

from ..parser.exceptions import UnknownElementTreeParseError
from .scte35_tags import SpliceInfoSection

if TYPE_CHECKING:
    from ..parser.mpd_tags import Event


class SCTE35Parser:
    """
    Parser class for SCTE35 XML information.
    Can parse SCTE35 XML from string using the from_string method.
    """

    @classmethod
    def from_string(cls, scte35_xml: str) -> SpliceInfoSection:
        """Generate a parsed SCTE35 object from a given string

        Args:
            scte35_xml (str): string representation of SCTE35 XML

        Returns:
            SpliceInfoSection: an object representing the SCTE35 information
        """
        try:
            root = etree.fromstring(scte35_xml)
        except Exception as err:
            raise UnknownElementTreeParseError() from err
        return SpliceInfoSection(root)

    @classmethod
    def from_element(cls, element: etree.Element) -> SpliceInfoSection:
        """Generate a parsed SCTE35 object from a given lxml Element

        Args:
            element (etree.Element): lxml Element containing SCTE35 information

        Returns:
            SpliceInfoSection: an object representing the SCTE35 information
        """
        return SpliceInfoSection(element)

    @classmethod
    def from_dash_event(cls, event: etree.Element) -> SpliceInfoSection:
        """Extract the SpliceInfoSection from a DASH event Element.
        The SpliceInfoSection must be a direct child of the Event element.

        Args:
            event (etree.Element): DASH event Element containing SCTE35 information

        Returns:
            SpliceInfoSection: an object representing the SCTE35 information

        Raises:
            UnknownElementTreeParseError: If no SpliceInfoSection is found as a direct child of the event
        """
        # Find the SpliceInfoSection element that is a direct child of the Event
        for child in event:
            if child.tag.endswith("SpliceInfoSection"):
                return SpliceInfoSection(child)
        raise UnknownElementTreeParseError(
            "No SpliceInfoSection found as direct child of DASH event"
        )

    @classmethod
    def from_event_tag(cls, event: "Event") -> SpliceInfoSection:
        """Extract the SpliceInfoSection from a DASH Event tag.
        The SpliceInfoSection must be a direct child of the Event element.

        Args:
            event (Event): DASH Event tag containing SCTE35 information

        Returns:
            SpliceInfoSection: an object representing the SCTE35 information

        Raises:
            UnknownElementTreeParseError: If no SpliceInfoSection is found as direct child of the event
        """
        # The Event tag has the lxml element as event.element
        return cls.from_dash_event(event.element)

    @classmethod
    def to_string(cls, scte35: SpliceInfoSection) -> str:
        """Generate a string XML from a given SCTE35 object

        Args:
            scte35 (SpliceInfoSection): SCTE35 object to convert to string

        Returns:
            str: string representation of the SCTE35 object
        """
        return etree.tostring(scte35.element).decode("utf-8")
