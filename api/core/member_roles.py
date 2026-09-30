"""Public membership grades stay separate from internal administrator permissions."""
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import PartnerStaff

GRADES = {"general": "일반회원", "mini": "미니회원", "partner": "협력업체"}
MINI_GROUP = "ILOVEMINI:미니회원"


def member_grade(user):
    if PartnerStaff.objects.filter(user=user, is_active=True, partner__is_active=True).exists():
        return "partner"
    if user.groups.filter(name=MINI_GROUP).exists():
        return "mini"
    return "general"


@transaction.atomic
def assign_member_grade(actor, user, grade):
    if not actor.is_active or not actor.is_superuser:
        raise PermissionDenied("회원 등급은 운영자만 변경할 수 있습니다.")
    if grade not in GRADES:
        raise ValidationError("알 수 없는 회원 등급입니다.")
    if grade == "partner" and not PartnerStaff.objects.filter(user=user, is_active=True, partner__is_active=True).exists():
        raise ValidationError("먼저 협력업체 담당자에 소속 업체를 연결해주세요.")
    group, _ = Group.objects.get_or_create(name=MINI_GROUP)
    if grade == "mini":
        user.groups.add(group)
    else:
        user.groups.remove(group)
    if grade in ("general", "mini"):
        PartnerStaff.objects.filter(user=user, is_active=True).update(is_active=False)
    return member_grade(user)
