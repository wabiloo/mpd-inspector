"""
Main module of the package, Parser class
"""

from re import Match, sub
from urllib.request import urlopen

from lxml import etree

from .exceptions import UnicodeDeclaredError, UnknownElementTreeParseError
from .mpd_tags import MPD
from ..scte35.scte35_tags import SpliceInfoSection

ENCODING_PATTERN = r"<\?.*?\s(encoding=[\"\']\S*[\"\']).*\?>"


class MPDParser:
    """
    Parser class, holds factories to work with manifest files.
    can parse:
    1. from string - using the from_string method
    2. from file - TBA
    3. from url - TBA
    """

    @classmethod
    def from_string(cls, manifest_as_string: str) -> MPD:
        """generate a parsed mpd object from a given string

        Args:
            manifest_as_string (str): string repr of a manifest file.

        Returns:
            an object representing the MPD tag and all it's XML goodies
        """
        # remove encoding declaration from manifest if exist
        encoding = []
        if "encoding" in manifest_as_string:

            def cut_and_burn(match: Match) -> str:
                """Helper to save the removed encoding"""
                encoding.append(match)
                return ""

            manifest_as_string = sub(ENCODING_PATTERN, cut_and_burn, manifest_as_string)
        try:
            root = etree.fromstring(manifest_as_string)
        except ValueError as err:
            if "Unicode" in err.args[0]:
                raise UnicodeDeclaredError() from err
        except Exception as err:
            raise UnknownElementTreeParseError() from err
        if encoding:
            return MPD(root, encoding=encoding[0].groups()[0])
        return MPD(root)

    @classmethod
    def from_file(cls, manifest_file_name: str) -> MPD:
        """
            Generate a parsed mpd object from a given file name
        Args:
            manifest_file_name (str): file name to parse

        Returns:
            an object representing the MPD tag and all it's XML goodies
        """
        try:
            tree = etree.parse(manifest_file_name)
        except ValueError as err:
            if "Unicode" in err.args[0]:
                raise UnicodeDeclaredError() from err
        except Exception as err:
            raise UnknownElementTreeParseError() from err
        return MPD(tree.getroot())

    @classmethod
    def from_url(cls, url: str) -> MPD:
        """
            Generate a parsed mpd object from a given URL
        Args:
            url (str): the url of the file to parse

        Returns:
            an object representing the MPD tag and all it's XML goodies
        """
        try:
            with urlopen(url) as manifest_file:
                tree = etree.parse(manifest_file)
        except ValueError as err:
            if "Unicode" in err.args[0]:
                raise UnicodeDeclaredError() from err
        except Exception as err:
            raise UnknownElementTreeParseError() from err
        return MPD(tree.getroot())

    @classmethod
    def to_string(cls, mpd: MPD) -> str:
        """generate a string xml from a given MPD tag object

        Args:
                mpd: MPD object created by one of the parser factories
        Returns:
                a string representation of the MPD object, xml formatted dash mpeg manifest
        """
        return etree.tostring(mpd.element).decode("utf-8")


class SCTE35Parser:
    """
    Parser class for SCTE35 XML information.
    Can parse SCTE35 XML from:
    1. string - using the from_string method
    2. file - using the from_file method
    3. url - using the from_url method
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
    def from_file(cls, file_name: str) -> SpliceInfoSection:
        """Generate a parsed SCTE35 object from a given file

        Args:
            file_name (str): path to the SCTE35 XML file

        Returns:
            SpliceInfoSection: an object representing the SCTE35 information
        """
        try:
            tree = etree.parse(file_name)
        except Exception as err:
            raise UnknownElementTreeParseError() from err
        return SpliceInfoSection(tree.getroot())

    @classmethod
    def from_url(cls, url: str) -> SpliceInfoSection:
        """Generate a parsed SCTE35 object from a given URL

        Args:
            url (str): URL of the SCTE35 XML file

        Returns:
            SpliceInfoSection: an object representing the SCTE35 information
        """
        try:
            with urlopen(url) as scte35_file:
                tree = etree.parse(scte35_file)
        except Exception as err:
            raise UnknownElementTreeParseError() from err
        return SpliceInfoSection(tree.getroot())

    @classmethod
    def to_string(cls, scte35: SpliceInfoSection) -> str:
        """Generate a string XML from a given SCTE35 object

        Args:
            scte35 (SpliceInfoSection): SCTE35 object to convert to string

        Returns:
            str: string representation of the SCTE35 object
        """
        return etree.tostring(scte35.element).decode("utf-8")
