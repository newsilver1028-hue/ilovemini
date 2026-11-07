from django.contrib import admin
from core.admin import AdminCalendarMixin

from .models import (
    ClassSession,
    Classroom,
    Device,
    GuardianLink,
    Organization,
    OrganizationAdministrator,
    PairingCode,
    RemoteCommand,
    Student,
    TeacherAssignment,
)


@admin.register(Organization)
class OrganizationAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("name", "kind", "external_code", "is_active")
    search_fields = ("name", "external_code")
    list_filter = ("kind", "is_active")


@admin.register(Classroom)
class ClassroomAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("name", "organization", "grade", "room", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("name", "organization__name")


@admin.register(Student)
class StudentAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("display_name", "student_code", "organization", "classroom", "is_active")
    list_filter = ("organization", "classroom", "is_active")
    search_fields = ("display_name", "student_code")


@admin.register(OrganizationAdministrator)
class OrganizationAdministratorAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("user", "organization", "created_at")
    list_filter = ("organization",)


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("user", "classroom", "created_by", "created_at")
    list_filter = ("classroom__organization", "classroom")


@admin.register(GuardianLink)
class GuardianLinkAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("user", "student", "verified_at", "created_at")
    list_filter = ("student__organization", "verified_at")


@admin.register(Device)
class DeviceAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("student", "platform", "permission_granted", "lock_active", "last_seen_at", "is_active")
    list_filter = ("platform", "permission_granted", "lock_active", "is_active")
    search_fields = ("student__display_name", "student__student_code", "label")
    readonly_fields = ("device_token_hash", "installation_id", "enrolled_at")


@admin.register(PairingCode)
class PairingCodeAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("student", "created_by", "expires_at", "used_at", "created_at")
    readonly_fields = ("code_hash", "created_at")


@admin.register(ClassSession)
class ClassSessionAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("classroom", "state", "started_by", "started_at", "ended_at")
    list_filter = ("state", "classroom__organization")


@admin.register(RemoteCommand)
class RemoteCommandAdmin(AdminCalendarMixin, admin.ModelAdmin):
    list_display = ("command_id", "device", "action", "state", "created_at", "expires_at", "responded_at")
    list_filter = ("action", "state", "device__platform")
    readonly_fields = ("command_id", "created_at", "responded_at")
