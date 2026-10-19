import json
from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from .models import PartnerStaff, WebPushSubscription


def _booking_staff(request):
    return PartnerStaff.objects.filter(
        user=request.user,
        is_active=True,
        partner__is_active=True,
        can_manage_bookings=True,
    )


@login_required
@require_POST
def web_push_subscribe(request):
    staff = list(_booking_staff(request).select_related("partner"))
    if not staff:
        return JsonResponse({"error": "예약 알림을 받을 수 있는 업체 담당자만 등록할 수 있습니다."}, status=403)
    try:
        data = json.loads(request.body or b"{}")
        endpoint = str(data.get("endpoint", "")).strip()
        keys = data.get("keys") or {}
        p256dh = str(keys.get("p256dh", "")).strip()
        auth = str(keys.get("auth", "")).strip()
    except (json.JSONDecodeError, AttributeError, TypeError):
        return JsonResponse({"error": "알림 구독 정보가 올바르지 않습니다."}, status=400)
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc or len(endpoint) > 2048 or not p256dh or not auth:
        return JsonResponse({"error": "브라우저 알림 구독 정보가 올바르지 않습니다."}, status=400)
    for membership in staff:
        WebPushSubscription.objects.update_or_create(
            partner=membership.partner,
            endpoint=endpoint,
            defaults={"user": request.user, "p256dh": p256dh, "auth": auth},
        )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def web_push_unsubscribe(request):
    try:
        endpoint = str(json.loads(request.body or b"{}").get("endpoint", "")).strip()
    except (json.JSONDecodeError, AttributeError, TypeError):
        return JsonResponse({"error": "알림 구독 정보가 올바르지 않습니다."}, status=400)
    if endpoint:
        WebPushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({"ok": True})


def partner_service_worker(request):
    script = """self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) {}
  const title = data.title || '아이러브미니 협력업체 알림';
  const options = { body: data.body || '새 예약 알림이 있습니다.', data: { url: data.url || '/partner-admin/' }, tag: data.tag || 'partner-booking', renotify: true };
  event.waitUntil(self.registration.showNotification(title, options));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = new URL(event.notification.data && event.notification.data.url || '/partner-admin/', self.location.origin).href;
  event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windows => {
    for (const client of windows) { if (client.url.startsWith(self.location.origin) && 'focus' in client) return client.navigate(target).then(() => client.focus()); }
    return clients.openWindow(target);
  }));
});
"""
    response = HttpResponse(script, content_type="application/javascript; charset=utf-8")
    response["Service-Worker-Allowed"] = "/partner-admin/"
    response["Cache-Control"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    return response
