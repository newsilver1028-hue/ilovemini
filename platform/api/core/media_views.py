"""Public, read-only delivery of image files uploaded through Django admin."""
import hashlib

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import AppContent, Partner, SeasonBanner


def uploaded_image_url(request, path, image_data):
    digest = hashlib.sha256(bytes(image_data)).hexdigest()[:16]
    url = f"{path}?v={digest}"
    return request.build_absolute_uri(url) if request else url


def _image_response(data, content_type):
    if not data or content_type not in {"image/png", "image/jpeg", "image/webp"}:
        return HttpResponse(status=404)
    response = HttpResponse(bytes(data), content_type=content_type)
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "public, max-age=300"
    response["Content-Disposition"] = "inline"
    return response


def app_content_image(request, pk):
    now = timezone.now()
    item = get_object_or_404(
        AppContent.objects.filter(is_active=True, starts_at__lte=now)
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now)),
        pk=pk,
    )
    return _image_response(item.image_data, item.image_content_type)


def season_banner_image(request, pk):
    now = timezone.now()
    banner = get_object_or_404(
        SeasonBanner.objects.filter(is_active=True, starts_at__lte=now)
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now)),
        pk=pk,
    )
    return _image_response(banner.image_data, banner.image_content_type)


def partner_image(request, pk, image_kind):
    partner = get_object_or_404(Partner, pk=pk, is_active=True)
    fields = {
        "storefront": (partner.storefront_photo_data, partner.storefront_photo_content_type),
        "representative": (partner.representative_photo_data, partner.representative_photo_content_type),
    }
    image = fields.get(image_kind)
    if image is None:
        return HttpResponse(status=404)
    return _image_response(*image)
