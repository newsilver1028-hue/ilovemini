from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import (
    PartnerBooking,
    PartnerScheduleBlock,
    PartnerScheduleException,
    PartnerServiceDuration,
    PartnerWeeklySchedule,
)


ACTIVE_BOOKING_STATUSES = (PartnerBooking.Status.REQUESTED, PartnerBooking.Status.CONFIRMED)


def service_duration(partner, service_name):
    config = PartnerServiceDuration.objects.filter(
        partner=partner, service_name__iexact=service_name.strip(), is_active=True
    ).first()
    return config.duration_minutes if config else 60


def opening_window(partner, day):
    exception = PartnerScheduleException.objects.filter(partner=partner, date=day).first()
    if exception:
        if exception.is_closed:
            return None
        return exception.opens_at, exception.closes_at, 30
    weekly = PartnerWeeklySchedule.objects.filter(partner=partner, weekday=day.weekday()).first()
    if not weekly or weekly.is_closed:
        return None
    return weekly.opens_at, weekly.closes_at, weekly.slot_interval_minutes


def _aware(day, clock):
    return timezone.make_aware(datetime.combine(day, clock), timezone.get_current_timezone())


def is_slot_available(partner, starts_at, duration_minutes, *, exclude_booking_id=None):
    local_start = timezone.localtime(starts_at)
    day = local_start.date()
    window = opening_window(partner, day)
    if window:
        opens_at, closes_at, interval = window
        end_at = starts_at + timedelta(minutes=duration_minutes)
        opening = _aware(day, opens_at)
        closing = _aware(day, closes_at)
        if starts_at < opening or end_at > closing:
            return False, "정비가 끝나는 시각까지 업체 운영시간 안에 들어오는 예약만 가능합니다."
        minutes_from_open = int((starts_at - opening).total_seconds() // 60)
        if minutes_from_open % interval or starts_at.second or starts_at.microsecond:
            return False, f"예약 시작 시각은 {interval}분 간격으로 선택해 주세요."
    end_at = starts_at + timedelta(minutes=duration_minutes)
    bookings = PartnerBooking.objects.filter(
        partner=partner, status__in=ACTIVE_BOOKING_STATUSES,
        scheduled_at__lt=end_at,
    )
    if exclude_booking_id:
        bookings = bookings.exclude(pk=exclude_booking_id)
    for booking in bookings.only("scheduled_at", "duration_minutes"):
        booking_end = booking.scheduled_at + timedelta(minutes=booking.duration_minutes or 60)
        if booking.scheduled_at < end_at and booking_end > starts_at:
            return False, BOOKING_OVERLAP_REASON
    for block in PartnerScheduleBlock.objects.filter(partner=partner, starts_at__lt=end_at, ends_at__gt=starts_at):
        return False, "업체 사정으로 예약이 막힌 시간입니다. 다른 시간을 선택해 주세요."
    return True, ""


def available_slots(partner, day, service_name):
    window = opening_window(partner, day)
    if not window:
        configured = PartnerWeeklySchedule.objects.filter(partner=partner).exists() or PartnerScheduleException.objects.filter(partner=partner, date=day).exists()
        return {"configured": configured,
                "duration_minutes": service_duration(partner, service_name), "slots": []}
    opens_at, closes_at, interval = window
    duration = service_duration(partner, service_name)
    current = _aware(day, opens_at)
    closing = _aware(day, closes_at)
    slots = []
    active_bookings = list(PartnerBooking.objects.filter(
        partner=partner, status__in=ACTIVE_BOOKING_STATUSES,
        scheduled_at__lt=closing,
    ).only("scheduled_at", "duration_minutes"))
    blocks = list(PartnerScheduleBlock.objects.filter(
        partner=partner, starts_at__lt=closing, ends_at__gt=current,
    ).only("starts_at", "ends_at"))
    while current + timedelta(minutes=duration) <= closing:
        end_at = current + timedelta(minutes=duration)
        busy = any(row.scheduled_at < end_at and row.scheduled_at + timedelta(minutes=row.duration_minutes or 60) > current for row in active_bookings)
        busy = busy or any(row.starts_at < end_at and row.ends_at > current for row in blocks)
        ok = not busy
        if ok and current > timezone.now():
            slots.append(timezone.localtime(current).isoformat())
        current += timedelta(minutes=interval)
    return {"configured": True, "duration_minutes": duration, "slots": slots}
