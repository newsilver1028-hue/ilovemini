from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import SeasonBanner


class SeasonBannerView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        banner = SeasonBanner.objects.filter(is_active=True, starts_at__lte=now).filter(
            Q(ends_at__isnull=True) | Q(ends_at__gt=now)
        ).first()
        data = None if banner is None else {
            "id": banner.pk, "title": banner.title, "subtitle": banner.subtitle,
            "image_url": banner.image_url if banner.image_url.startswith("https://") else "",
            "asset_key": banner.asset_key,
            "duration_seconds": min(5, max(1, banner.duration_seconds)),
        }
        response = Response({"banner": data})
        response["Cache-Control"] = "no-store"
        return response
