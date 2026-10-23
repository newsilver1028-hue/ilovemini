from datetime import timedelta
from django import template
from django.db.models import Sum
from django.utils import timezone
from core.models import PartnerBooking, LedgerEntry, PointTransaction

register = template.Library()

@register.inclusion_tag('admin/operations_summary.html', takes_context=True)
def operations_summary(context):
    if not context['request'].user.is_superuser:
        return {}
    today = timezone.localdate()
    bookings = PartnerBooking.objects.filter(scheduled_at__date=today)
    records = LedgerEntry.objects.filter(source='partner', entry_date=today)
    points = PointTransaction.objects.filter(created_at__date=today)
    return {
        'visible': True, 'today': today,
        'statuses': [(label, bookings.filter(status=value).count()) for value, label in PartnerBooking.Status.choices],
        'paid': records.aggregate(total=Sum('amount_krw'))['total'] or 0,
        'earned': points.filter(points_delta__gt=0).aggregate(total=Sum('points_delta'))['total'] or 0,
        'spent': abs(points.filter(points_delta__lt=0).aggregate(total=Sum('points_delta'))['total'] or 0),
        'overdue': PartnerBooking.objects.filter(status='requested', requested_at__lt=timezone.now()-timedelta(hours=24)).count(),
        'unrecorded': PartnerBooking.objects.filter(status='confirmed', scheduled_at__lt=timezone.now()).count(),
    }
