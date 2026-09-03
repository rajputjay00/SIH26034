import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional

INITIAL_CHAIN_HASH = "0" * 64

def compute_sha256_bytes(content: bytes) -> str:
    """Compute SHA-256 hex digest of raw binary content."""
    hasher = hashlib.sha256()
    hasher.update(content)
    return hasher.hexdigest()

def compute_sha256_str(content: str) -> str:
    """Compute SHA-256 hex digest of string content."""
    return compute_sha256_bytes(content.encode("utf-8"))

def canonicalize_json(data: Optional[Dict[str, Any]]) -> str:
    """Produce deterministic canonical JSON string with sorted keys."""
    if data is None:
        return "{}"
    return json.dumps(data, sort_keys=True, separators=(',', ':'))

def compute_audit_entry_hash(
    previous_hash: str,
    audit_id: str,
    inspection_id: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    timestamp_iso: str,
    metadata_json: Optional[Dict[str, Any]] = None
) -> str:
    """
    Compute cryptographic SHA-256 hash for an append-only audit chain entry.
    Ensures complete hash-link integrity across historical events.
    """
    canonical_meta = canonicalize_json(metadata_json)
    raw_payload = f"{previous_hash}|{audit_id}|{inspection_id}|{actor_id}|{action}|{entity_type}|{entity_id}|{timestamp_iso}|{canonical_meta}"
    return compute_sha256_str(raw_payload)
