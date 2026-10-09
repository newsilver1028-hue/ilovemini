import json
import logging
from firebase_admin import credentials, messaging
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import PartnerStaff

logger = logging.getLogger(__name__)


def _ensure_firebase():
    import firebase_admin
    try:
        firebase_admin.get_app()
    except ValueError:
        if not getattr(settings, "FCM_ENABLED", False):
            return False
        credentials_json = getattr(settings, "FCM_CREDENTIALS_JSON", "").strip()
        credential = credentials.Certificate(json.loads(credentials_json)) if credentials_json else None
        firebase_admin.initialize_app(credential)
    return getattr(settings, "FCM_ENABLED", False)


def send_reminder_notification(reminder, trigger):
    if not _ensure_firebase():
        return 0
    ownership = reminder.vehicle.current_ownership
    if ownership is None or reminder.created_at < ownership.started_at:
        return 0
    devices = list(ownership.user.push_devices.all())
    if not devices:
        return 0

    vehicle_name = reminder.vehicle.nickname or reminder.vehicle.model_name
    if trigger == "odometer":
        current_km = reminder.vehicle.current_odometer_km or reminder.due_odometer_km
        body = f"{vehicle_name}: {reminder.title} 점검 주행거리에 도달했습니다 ({current_km:,}km)."
    else:
        body = f"{vehicle_name}: {reminder.title} 예정일입니다."
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title="아이러브미니 정비 알림",
            body=body,
        ),
        data={"type": "reminder", "reminder_id": str(reminder.pk), "trigger": trigger},
        tokens=[device.installation_id for device in devices],
    )
    result = messaging.send_each_for_multicast(message)
    invalid_tokens = []
    for device, response in zip(devices, result.responses):
        if response.success:
            continue
        error_code = getattr(response.exception, "code", "")
        if error_code in {"installation-id-not-registered", "registration-token-not-registered", "invalid-registration-token"}:
            invalid_tokens.append(device.pk)
    if invalid_tokens:
        type(devices[0]).objects.filter(pk__in=invalid_tokens).delete()
    return result.success_count


def send_booking_notification(booking):
    if not _ensure_firebase():
        return 0
    user_ids = PartnerStaff.objects.filter(
        partner=booking.partner, is_active=True, can_manage_bookings=True,
    ).values_list("user_id", flat=True)
    devices = list(get_user_model().objects.filter(pk__in=user_ids).values_list("push_devices__installation_id", flat=True))
    devices = [value for value in devices if value]
    if not devices:
        return 0
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=f"새 예약 요청 · {booking.partner.name}" + (f" · {booking.partner.branch_label}" if booking.partner.branch_label else ""),
            body=f"{booking.partner.region + ' · ' if booking.partner.region else ''}{booking.scheduled_at:%m월 %d일 %H:%M} · {booking.service_type}",
        ),
        data={"type": "partner_booking", "booking_id": str(booking.pk)},
        tokens=devices,
    )
    return messaging.send_each_for_multicast(message).success_count


def send_booking_status_notification(booking):
    if not _ensure_firebase():
        return 0
    devices = list(booking.customer.push_devices.all())
    if not devices:
        return 0
    status_text = booking.get_status_display()
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=f"예약 상태 변경 · {booking.partner.name}" + (f" · {booking.partner.branch_label}" if booking.partner.branch_label else ""),
            body=f"{booking.scheduled_at:%m월 %d일 %H:%M} · {status_text}",
        ),
        data={"type": "partner_booking_status", "booking_id": str(booking.pk), "status": booking.status},
        tokens=[device.installation_id for device in devices],
    )
    return messaging.send_each_for_multicast(message).success_count


def send_booking_cancel_notification(booking):
    if not _ensure_firebase():
        return 0
    user_ids = PartnerStaff.objects.filter(
        partner=booking.partner, is_active=True, can_manage_bookings=True,
    ).values_list("user_id", flat=True)
    devices = list(get_user_model().objects.filter(pk__in=user_ids).values_list("push_devices__installation_id", flat=True))
    devices = [value for value in devices if value]
    if not devices:
        return 0
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=f"예약 취소 · {booking.partner.name}" + (f" · {booking.partner.branch_label}" if booking.partner.branch_label else ""),
            body=f"{booking.partner.region + ' · ' if booking.partner.region else ''}{booking.scheduled_at:%m월 %d일 %H:%M} · {booking.service_type}",
        ),
        data={"type": "partner_booking_status", "booking_id": str(booking.pk), "status": booking.status},
        tokens=devices,
    )
    return messaging.send_each_for_multicast(message).success_count


def send_record_correction_notification(correction_request):
    """Notify staff who can verify records when a member requests a correction."""
    if not _ensure_firebase():
        return 0
    entry = correction_request.entry
    partner = entry.partner
    if partner is None or not partner.is_active:
        return 0
    staff_ids = PartnerStaff.objects.filter(
        partner=partner, is_active=True, can_verify_records=True,
    ).values_list("user_id", flat=True)
    tokens = list(
        get_user_model().objects.filter(pk__in=staff_ids)
        .values_list("push_devices__installation_id", flat=True)
    )
    tokens = list(dict.fromkeys(token for token in tokens if token))
    if not tokens:
        return 0

    vehicle = entry.vehicle
    vehicle_name = vehicle.nickname or vehicle.model_name
    record_name = entry.description or entry.get_kind_display()
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=f"정비 기록 정정 요청 · {partner.name}",
            body=f"{vehicle_name} · {record_name}: {correction_request.reason}",
        ),
        data={
            "type": "record_correction",
            "request_id": str(correction_request.pk),
            "entry_id": str(entry.pk),
            "partner_id": str(partner.pk),
        },
        tokens=tokens,
    )
    try:
        return messaging.send_each_for_multicast(message).success_count
    except Exception:
        # A push provider outage must not undo the member's saved request.
        logger.exception("Failed to send record correction push (request_id=%s)", correction_request.pk)
        return 0
