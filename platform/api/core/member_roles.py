"""Public membership grades stay separate from internal administrator permissions."""
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import AppReviewAccount, Partner, PartnerStaff

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
def assign_member_grade(actor, user, grade, *, partner=None, can_manage_bookings=False, can_verify_records=False):
    if not actor.is_active or not actor.is_superuser:
        raise PermissionDenied("회원 등급은 운영자만 변경할 수 있습니다.")
    if grade not in GRADES:
        raise ValidationError("알 수 없는 회원 등급입니다.")
    if AppReviewAccount.objects.filter(user=user).exists() and grade != "general":
        raise ValidationError("앱 심사용 계정은 일반회원 권한으로만 유지할 수 있습니다.")
    if grade == "partner":
        if partner is not None:
            if not isinstance(partner, Partner) or not partner.is_active:
                raise ValidationError("운영 중인 협력업체를 선택해 주세요.")
            # A member belongs to one active workshop at a time. This keeps all
            # partner-admin queries scoped to the shop the operator selected.
            PartnerStaff.objects.filter(user=user, is_active=True).exclude(partner=partner).update(is_active=False)
            PartnerStaff.objects.update_or_create(
                user=user,
                partner=partner,
                defaults={
                    "is_active": True,
                    "can_manage_bookings": can_manage_bookings,
                    "can_verify_records": can_verify_records,
                },
            )
        elif not PartnerStaff.objects.filter(user=user, is_active=True, partner__is_active=True).exists():
            raise ValidationError("협력업체 등급을 적용하려면 소속 업체와 권한을 함께 지정해 주세요.")
    group, _ = Group.objects.get_or_create(name=MINI_GROUP)
    if grade == "mini":
        user.groups.add(group)
    else:
        user.groups.remove(group)
    if grade in ("general", "mini"):
        PartnerStaff.objects.filter(user=user, is_active=True).update(is_active=False)
    return member_grade(user)
