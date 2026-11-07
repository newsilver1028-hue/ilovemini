from django.urls import path

from .views import (
    ClassSessionEndView,
    ClassSessionStartView,
    DeviceEndpoint,
    DeviceEnrollView,
    DeviceHeartbeatView,
    OnClassTokenObtainPairView,
    PairingCodeView,
    RosterView,
    RoleSummaryView,
    StudentCommandView,
)

urlpatterns = [
    path("auth/token/", OnClassTokenObtainPairView.as_view(), name="onclass_token_obtain"),
    path("auth/me/", RoleSummaryView.as_view(), name="onclass_role_summary"),
    path("roster/", RosterView.as_view(), name="onclass_roster"),
    path("students/<int:student_id>/pairing-code/", PairingCodeView.as_view(), name="onclass_pairing_code"),
    path("students/<int:student_id>/commands/", StudentCommandView.as_view(), name="onclass_student_command"),
    path("classes/<int:classroom_id>/sessions/", ClassSessionStartView.as_view(), name="onclass_session_start"),
    path("sessions/<int:session_id>/end/", ClassSessionEndView.as_view(), name="onclass_session_end"),
    path("devices/enroll/", DeviceEnrollView.as_view(), name="onclass_device_enroll"),
    path("devices/commands/", DeviceEndpoint.as_view(), name="onclass_device_commands"),
    path("devices/heartbeat/", DeviceHeartbeatView.as_view(), name="onclass_device_heartbeat"),
]
