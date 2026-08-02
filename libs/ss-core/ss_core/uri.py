"""SovereignStack URI scheme parser.

URI format: ``ss://<authority>/<resource-type>/<resource-id>``

Examples:
    ss://acme.corp/audit/evt-2026-07-31-001
    ss://globex.inc/key/ed25519-pubkey-abc123
    ss://localhost/cas/sha256:abcdef...
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Self

from ss_core.errors import UriParseError

# Allowed characters in each segment: alphanumeric, hyphens, dots, colons, underscores.
_AUTHORITY_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.\-_]*$")
_RESOURCE_TYPE_RE = re.compile(r"^[a-z][a-z0-9\-_]*$")
# Resource ID is more permissive — allows colons for content hashes (sha256:...).
_RESOURCE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.\-_:]*$")

_SCHEME = "ss"


@dataclass(frozen=True, slots=True)
class SsUri:
    """Parsed SovereignStack URI.

    Attributes:
        authority: The organization or node identifier (e.g. ``acme.corp``).
        resource_type: The resource category (e.g. ``audit``, ``key``, ``cas``).
        resource_id: The specific resource identifier.
    """

    authority: str
    resource_type: str
    resource_id: str

    def __post_init__(self) -> None:
        if not _AUTHORITY_RE.match(self.authority):
            raise UriParseError(
                f"Invalid authority: {self.authority!r}. "
                "Must start with alphanumeric and contain only [a-zA-Z0-9.\\-_]"
            )
        if not _RESOURCE_TYPE_RE.match(self.resource_type):
            raise UriParseError(
                f"Invalid resource_type: {self.resource_type!r}. "
                "Must be lowercase, start with a letter, and contain only [a-z0-9\\-_]"
            )
        if not _RESOURCE_ID_RE.match(self.resource_id):
            raise UriParseError(
                f"Invalid resource_id: {self.resource_id!r}. "
                "Must start with alphanumeric and contain only [a-zA-Z0-9.\\-_:]"
            )

    def __str__(self) -> str:
        return f"{_SCHEME}://{self.authority}/{self.resource_type}/{self.resource_id}"

    def __repr__(self) -> str:
        return f"SsUri({self})"

    @classmethod
    def parse(cls, uri_string: str) -> Self:
        """Parse a SovereignStack URI string.

        Args:
            uri_string: A string in the form ``ss://<authority>/<type>/<id>``.

        Returns:
            A validated ``SsUri`` instance.

        Raises:
            UriParseError: If the string is malformed or contains invalid segments.
        """
        if not uri_string.startswith(f"{_SCHEME}://"):
            raise UriParseError(
                f"URI must start with '{_SCHEME}://', got: {uri_string!r}"
            )

        remainder = uri_string[len(f"{_SCHEME}://"):]
        parts = remainder.split("/")

        if len(parts) != 3:
            raise UriParseError(
                f"URI must have exactly 3 path segments "
                f"(authority/type/id), got {len(parts)}: {uri_string!r}"
            )

        authority, resource_type, resource_id = parts

        if not authority:
            raise UriParseError(f"Empty authority in URI: {uri_string!r}")
        if not resource_type:
            raise UriParseError(f"Empty resource_type in URI: {uri_string!r}")
        if not resource_id:
            raise UriParseError(f"Empty resource_id in URI: {uri_string!r}")

        return cls(
            authority=authority,
            resource_type=resource_type,
            resource_id=resource_id,
        )


def parse_uri(uri_string: str) -> SsUri:
    """Convenience function: parse a SovereignStack URI string.

    Equivalent to ``SsUri.parse(uri_string)``.
    """
    return SsUri.parse(uri_string)
