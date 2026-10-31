"""Public membership grades stay separate from internal administrator permissions."""
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import AppReviewAccount, PartnerStaff

GRADES = {"general": "일반회원", "mini": "미니회원", "partner": "협력업체"}
MINI_GROUP = "ILOVEMINI:미니회원"


def member_grade(user):
    if AppReviewAccount.objects.filter(user=user, is_active=True).exists():
        return "general"
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
    if AppReviewAccount.objects.filter(user=user).exists() and grade != "general":
        raise ValidationError("앱 심사용 계정은 일반회원 권한으로만 유지할 수 있습니다.")
    if grade == "partner" and not PartnerStaff.objects.filter(user=user, is_active=True, partner__is_active=True).exists():
        raise ValidationError("먼저 관리자 메뉴의 ‘협력업체 담당자’에서 이 회원의 소속 업체와 담당 권한을 지정하고 ‘활성화’한 뒤 다시 적용해 주세요.")
    group, _ = Group.objects.get_or_create(name=MINI_GROUP)
    if grade == "mini":
        user.groups.add(group)
    else:
        user.groups.remove(group)
    if grade in ("general", "mini"):
        PartnerStaff.objects.filter(user=user, is_active=True).update(is_active=False)
    return member_grade(user)
