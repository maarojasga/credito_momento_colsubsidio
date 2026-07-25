"""Caché en disco para llamadas de proveedor.

Clave: (provider_id, version, hash(inputs)). La geocodificación se cachea
agresivamente porque muchas direcciones caen en la misma manzana.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def cache_key(provider_id: str, version: str, inputs: dict) -> str:
    payload = json.dumps(inputs, sort_keys=True, ensure_ascii=False)
    h = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"{provider_id}@{version}:{h}"


class DiskCache:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict | None:
        raise NotImplementedError

    def put(self, key: str, value: dict) -> None:
        raise NotImplementedError
