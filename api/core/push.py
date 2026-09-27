from firebase_admin import messaging


def send_reminder_notification(reminder, trigger):
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
        fids=[device.installation_id for device in devices],
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
