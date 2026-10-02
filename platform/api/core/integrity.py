import hashlib
import hmac
import json

from django.conf import settings


def ledger_record_payload(entry):
    payload = {
        "record_id": entry.pk,
        "vehicle_id": entry.vehicle_id,
        "source": entry.source,
        "kind": entry.kind,
        "entry_date": entry.entry_date.isoformat(),
        "odometer_km": entry.odometer_km,
        "amount_krw": entry.amount_krw,
        "description": entry.description,
        "quantity_liters": str(entry.quantity_liters) if entry.quantity_liters is not None else None,
        "partner_id": entry.partner_id,
        "verified_by_id": entry.verified_by_id,
        "verified_at": entry.verified_at.isoformat() if entry.verified_at else None,
        "part_number": entry.part_number,
        "evidence_url": entry.evidence_url,
    }
    if entry.corrects_id is not None or entry.correction_reason:
        payload["corrects_id"] = entry.corrects_id
        payload["correction_reason"] = entry.correction_reason
    return payload


def _sign(payload):
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hmac.new(settings.LEDGER_INTEGRITY_KEY.encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()


def ledger_record_hash(entry):
    return _sign(ledger_record_payload(entry))


def legacy_ledger_record_hash(entry):
    """Verify records signed before record IDs and source were added to the payload."""
    return _sign({
        "vehicle_id": entry.vehicle_id,
        "kind": entry.kind,
        "entry_date": entry.entry_date.isoformat(),
        "odometer_km": entry.odometer_km,
        "amount_krw": entry.amount_krw,
        "description": entry.description,
        "quantity_liters": str(entry.quantity_liters) if entry.quantity_liters is not None else None,
        "partner_id": entry.partner_id,
        "verified_by_id": entry.verified_by_id,
        "verified_at": entry.verified_at.isoformat() if entry.verified_at else None,
        "part_number": entry.part_number,
        "evidence_url": entry.evidence_url,
    })
