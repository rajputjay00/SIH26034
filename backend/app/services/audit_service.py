import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.domain import AuditEntry
from app.audit.hasher import INITIAL_CHAIN_HASH, compute_audit_entry_hash

def _get_iso_timestamp(ts) -> str:
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%dT%H:%M:%S")
    return str(ts)


class AuditService:
    @staticmethod
    def record_event(
        db: Session,
        inspection_id: str,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Record a new hash-chained audit event.
        Fetches the latest audit entry hash for the given inspection case
        and links the new entry deterministically.
        """
        last_entry = db.query(AuditEntry)\
            .filter(AuditEntry.inspection_id == inspection_id)\
            .order_by(AuditEntry.timestamp.desc(), AuditEntry.audit_id.desc())\
            .first()
            
        previous_hash = last_entry.entry_hash if last_entry else INITIAL_CHAIN_HASH
        audit_id = str(uuid.uuid4())
        timestamp_dt = datetime.now(timezone.utc)
        timestamp_iso = _get_iso_timestamp(timestamp_dt)

        entry_hash = compute_audit_entry_hash(
            previous_hash=previous_hash,
            audit_id=audit_id,
            inspection_id=inspection_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp_iso=timestamp_iso,
            metadata_json=metadata
        )

        audit_entry = AuditEntry(
            audit_id=audit_id,
            inspection_id=inspection_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=timestamp_dt,
            metadata_json=metadata,
            previous_hash=previous_hash,
            entry_hash=entry_hash
        )

        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def verify_chain(db: Session, inspection_id: str) -> Tuple[bool, int, Optional[int], str]:
        """
        Verifies cryptographic integrity of the append-only audit chain for an inspection case.
        Returns: (is_valid, total_entries, corrupted_sequence_index, detail_message)
        """
        entries = db.query(AuditEntry)\
            .filter(AuditEntry.inspection_id == inspection_id)\
            .order_by(AuditEntry.timestamp.asc(), AuditEntry.audit_id.asc())\
            .all()

        if not entries:
            return True, 0, None, "No audit entries exist for this inspection case."

        expected_previous_hash = INITIAL_CHAIN_HASH

        for idx, entry in enumerate(entries):
            # Check previous hash link
            if entry.previous_hash != expected_previous_hash:
                return False, len(entries), idx, (
                    f"Audit chain broken at index {idx}: previous_hash '{entry.previous_hash}' "
                    f"does not match expected previous hash '{expected_previous_hash}'."
                )

            # Re-compute current entry hash
            recomputed_hash = compute_audit_entry_hash(
                previous_hash=entry.previous_hash,
                audit_id=entry.audit_id,
                inspection_id=entry.inspection_id,
                actor_id=entry.actor_id,
                action=entry.action,
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                timestamp_iso=_get_iso_timestamp(entry.timestamp),
                metadata_json=entry.metadata_json
            )

            if recomputed_hash != entry.entry_hash:
                return False, len(entries), idx, (
                    f"Audit entry hash mismatch at index {idx}: stored '{entry.entry_hash}' "
                    f"does not match recomputed hash '{recomputed_hash}'."
                )

            expected_previous_hash = entry.entry_hash

        return True, len(entries), None, "Audit chain integrity verified successfully."


    @staticmethod
    def get_case_audit_history(db: Session, inspection_id: str) -> List[AuditEntry]:
        """Retrieves audit entries for an inspection case in chronological order."""
        return db.query(AuditEntry)\
            .filter(AuditEntry.inspection_id == inspection_id)\
            .order_by(AuditEntry.timestamp.asc())\
            .all()
