from django.conf import settings
from django.db.models import Q
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from .models import Device, digest_secret


def is_master_owner(user):
    owner_email = str(getattr(settings, "ONCLASS_MASTER_EMAIL", "")).strip().casefold()
    user_email = str(getattr(user, "email", "")).strip().casefold()
    return bool(owner_email and user_email and user_email == owner_email and user.is_authenticated)


def visible_students(user):
    from .models import GuardianLink, OrganizationAdministrator, Student, TeacherAssignment

    if is_master_owner(user):
        return Student.objects.filter(is_active=True)
    org_ids = OrganizationAdministrator.objects.filter(user=user).values_list("organization_id", flat=True)
    class_ids = TeacherAssignment.objects.filter(user=user).values_list("classroom_id", flat=True)
    guardian_student_ids = GuardianLink.objects.filter(user=user, verified_at__isnull=False).values_list("student_id", flat=True)
    return Student.objects.filter(is_active=True).filter(
        Q(organization_id__in=org_ids) | Q(classroom_id__in=class_ids) | Q(pk__in=guardian_student_ids)
    ).distinct()


def can_control_student(user, student, *, class_wide=False):
    from .models import GuardianLink, OrganizationAdministrator, TeacherAssignment

    if is_master_owner(user):
        return True
    if OrganizationAdministrator.objects.filter(user=user, organization=student.organization).exists():
        return True
    if TeacherAssignment.objects.filter(user=user, classroom=student.classroom).exists():
        return True
    if not class_wide and GuardianLink.objects.filter(
        user=user, student=student, verified_at__isnull=False
    ).exists():
        return True
    return False


def can_control_class(user, classroom):
    from .models import OrganizationAdministrator, TeacherAssignment

    if is_master_owner(user):
        return True
    return OrganizationAdministrator.objects.filter(
        user=user, organization=classroom.organization
    ).exists() or TeacherAssignment.objects.filter(user=user, classroom=classroom).exists()


class DeviceTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw = request.headers.get("X-OnClass-Device-Token", "").strip()
        if not raw:
            return None
        try:
            device = Device.objects.select_related("student").get(
                device_token_hash=digest_secret(raw), is_active=True, student__is_active=True
            )
        except Device.DoesNotExist:
            raise AuthenticationFailed("기기 등록 정보를 확인할 수 없습니다.")
        return device, None


class IsRegisteredDevice(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, Device)
