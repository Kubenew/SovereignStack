"""SovereignStack client — resolves objects, manages state, emits events."""

import json
from typing import Optional
from sovereignstack.objects import SovereignObject
from sovereignstack.uri import parse_uri, UriScheme


class SovereignClient:
    """In-memory client for SovereignStack object resolution.

    Usage:
        client = SovereignClient()
        client.register(my_object)
        resolved = client.resolve("payment://cbdc/ecb/pacs008-001")
    """

    def __init__(self):
        self._store: dict[str, SovereignObject] = {}
        self._events: list[dict] = []

    def register(self, obj: SovereignObject) -> None:
        self._store[obj.uri] = obj
        self._emit("object.registered", obj.uri)

    def resolve(self, uri: str) -> Optional[SovereignObject]:
        return self._store.get(uri)

    def resolve_or_raise(self, uri: str) -> SovereignObject:
        obj = self._store.get(uri)
        if obj is None:
            raise KeyError(f"Object not found: {uri}")
        return obj

    def list_by_scheme(self, scheme: UriScheme) -> list[SovereignObject]:
        prefix = f"{scheme.value}://"
        return [o for o in self._store.values() if o.uri.startswith(prefix)]

    def list_all(self) -> list[SovereignObject]:
        return list(self._store.values())

    def export_provenance(self) -> dict:
        entries = []
        for obj in self._store.values():
            entries.append({
                "uri": obj.uri,
                "kind": obj.kind,
                "signature": obj.signature,
                "created_at": obj.created_at,
            })
        return {
            "entries": entries,
            "total": len(entries),
            "events": self._events[-100:],
        }

    def export_provenance_json(self) -> str:
        return json.dumps(self.export_provenance(), indent=2)

    def _emit(self, event_type: str, uri: str) -> None:
        from datetime import datetime, timezone
        self._events.append({
            "type": event_type,
            "uri": uri,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @property
    def object_count(self) -> int:
        return len(self._store)

    @property
    def event_count(self) -> int:
        return len(self._events)
