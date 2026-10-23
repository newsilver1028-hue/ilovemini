import logging
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ServiceEstimate, MaintenanceRecommendation

logger=logging.getLogger(__name__)

@receiver(post_save, sender=ServiceEstimate)
@receiver(post_save, sender=MaintenanceRecommendation)
def notify_member(sender,instance,created,**kwargs):
    if not created: return
    is_estimate=sender is ServiceEstimate
    if is_estimate and instance.status!='sent': return
    member=instance.booking.customer if is_estimate else instance.member
    kind='service_estimate' if is_estimate else 'maintenance_recommendation'
    title='정비 견적이 도착했습니다' if is_estimate else '다음 교체 안내가 도착했습니다'
    identifier=instance.pk
    def send():
        try:
            from .push import _ensure_firebase
            from firebase_admin import messaging
            if not _ensure_firebase(): return
            tokens=list(member.push_devices.values_list('installation_id',flat=True))
            for start in range(0,len(tokens),500):
                messaging.send_each_for_multicast(messaging.MulticastMessage(notification=messaging.Notification(title=title,body='MY에서 내용을 확인하고 응답해 주세요.'),data={'type':kind,'request_id':str(identifier)},tokens=tokens[start:start+500]))
        except Exception:
            logger.exception('Phase one notification failed: type=%s id=%s',kind,identifier)
    transaction.on_commit(send)
