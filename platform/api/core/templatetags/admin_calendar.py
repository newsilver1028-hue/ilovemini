from datetime import date, datetime, time, timedelta

from django import template
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

register = template.Library()


@register.inclusion_tag("admin/core/admin_mini_calendar.html", takes_context=True)
def mini_admin_calendar(context, cl):
    model_admin = getattr(cl, "model_admin", None)
    field_name = getattr(cl, "date_hierarchy", None)
    if not model_admin or not field_name or cl.opts.model_name in {"partnerbooking", "ledgerentry"}:
        return {"show_calendar": False}

    today = timezone.localdate()
    request = context.get("request")
    params = request.GET if request else {}
    try:
        year = int(params.get(f"{field_name}__year", today.year))
        month = int(params.get(f"{field_name}__month", today.month))
        month_start = date(year, month, 1)
    except (TypeError, ValueError):
        month_start = today.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    grid_start = month_start - timedelta(days=month_start.weekday())
    final_day = next_month - timedelta(days=1)
    grid_end = final_day + timedelta(days=6 - final_day.weekday())

    model_field = cl.opts.get_field(field_name)
    if getattr(model_field, "get_internal_type", lambda: "")() in {"DateTimeField", "DateField"}:
        if model_field.get_internal_type() == "DateTimeField":
            lower = timezone.make_aware(datetime.combine(month_start, time.min))
            upper = timezone.make_aware(datetime.combine(next_month, time.min))
        else:
            lower, upper = month_start, next_month
        counts = (
            cl.queryset.filter(**{f"{field_name}__gte": lower, f"{field_name}__lt": upper})
            .annotate(_calendar_day=TruncDate(field_name))
            .values("_calendar_day")
            .annotate(_count=Count("pk"))
        )
    else:
        return {"show_calendar": False}
    counts_by_day = {row["_calendar_day"]: row["_count"] for row in counts if row["_calendar_day"]}

    remove = [f"{field_name}__year", f"{field_name}__month", f"{field_name}__day"]

    def query_for(day):
        return cl.get_query_string({
            f"{field_name}__year": day.year,
            f"{field_name}__month": day.month,
            f"{field_name}__day": day.day,
        }, remove)

    def month_query(day):
        return cl.get_query_string({
            f"{field_name}__year": day.year,
            f"{field_name}__month": day.month,
        }, remove)

    weeks = []
    current = grid_start
    while current <= grid_end:
        week = []
        for _ in range(7):
            week.append({
                "date": current,
                "in_month": current.month == month_start.month,
                "is_today": current == today,
                "count": counts_by_day.get(current, 0),
                "url": query_for(current),
            })
            current += timedelta(days=1)
        weeks.append(week)

    return {
        "show_calendar": True,
        "calendar_month": month_start,
        "calendar_weeks": weeks,
        "calendar_weekdays": ["월", "화", "수", "목", "금", "토", "일"],
        "calendar_prev_url": month_query((month_start - timedelta(days=1)).replace(day=1)),
        "calendar_next_url": month_query(next_month),
        "calendar_today_url": month_query(today.replace(day=1)),
        "calendar_field_label": model_field.verbose_name,
    }
