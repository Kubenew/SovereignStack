"""Identity mapping — Morpheus users/service accounts to SovereignStack agents.

Maintains an agent registry (``agent://uri -> Ed25519 public key hex``) and a
binding table (Morpheus user name -> agent URI). Request signatures are
verified here before any authorization work begins.
"""

from __future__ import annotations

from typing import Optional

from crypto import canonical_json, verify


class IdentityMapper:
    def __init__(self) -> None:
        self._keys: dict[str, str] = {}
        self._bindings: dict[str, str] = {}

    def register(self, agent_uri: str, public_key_hex: str) -> None:
        """Register an agent's public key."""
        self._keys[agent_uri] = public_key_hex

    def bind(self, morpheus_user: str, agent_uri: str) -> None:
        """Bind a Morpheus user/service-account name to an agent URI."""
        self._bindings[morpheus_user] = agent_uri

    def resolve_agent(self, morpheus_user: str) -> Optional[str]:
        """Return the bound ``agent://`` URI for a Morpheus user."""
        return self._bindings.get(morpheus_user)

    def public_key(self, agent_uri: str) -> Optional[str]:
        """Return the registered public key for an agent."""
        return self._keys.get(agent_uri)

    def verify_request(
        self, agent_uri: str, message: dict, signature_hex: str
    ) -> tuple[bool, str]:
        """Verify an agent's signature over a canonical request message.

        Returns ``(verified, reason)``.
        """
        pk = self._keys.get(agent_uri)
        if pk is None:
            return False, f"identity://{agent_uri} not registered"
        if not verify(canonical_json(message), signature_hex, pk):
            return False, f"signature invalid for {agent_uri}"
        return True, f"signature verified for {agent_uri}"

    def verify_message(
        self, agent_uri: str, message_bytes: bytes, signature_hex: str
    ) -> bool:
        pk = self._keys.get(agent_uri)
        if pk is None:
            return False
        return verify(message_bytes, signature_hex, pk)
