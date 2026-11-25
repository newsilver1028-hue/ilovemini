"""Default weekly opening hours for newly registered workshops."""
from datetime import time
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Partner, PartnerWeeklySchedule


@receiver(post_save, sender=Partner, dispatch_uid="partner-default-weekly-hours")
def create_default_weekly_hours(sender, instance, created, raw=False, using="default", **kwargs):
    if not created or raw:
        return
    PartnerWeeklySchedule.objects.using(using).bulk_create([
        PartnerWeeklySchedule(partner_id=instance.pk, weekday=day, opens_at=time(9),
            closes_at=time(18), slot_interval_minutes=30, is_closed=False)
        for day in range(7)
    ], ignore_conflicts=True)
