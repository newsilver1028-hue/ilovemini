from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

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
    digest_secret,
)

User = get_user_model()


class OnClassAccessScopeTests(APITestCase):
    def setUp(self):
        self.school = Organization.objects.create(name="고산하늘초등학교", kind=Organization.Kind.SCHOOL)
        self.other_school = Organization.objects.create(name="다른 학교", kind=Organization.Kind.SCHOOL)
        self.class_a = Classroom.objects.create(organization=self.school, name="5학년 1반", grade="5", room="1")
        self.class_b = Classroom.objects.create(organization=self.school, name="5학년 2반", grade="5", room="2")
        self.other_class = Classroom.objects.create(organization=self.other_school, name="5학년 1반", grade="5", room="1")
        self.student_a = Student.objects.create(organization=self.school, classroom=self.class_a, student_code="5-1-01", display_name="학생 가")
        self.student_b = Student.objects.create(organization=self.school, classroom=self.class_b, student_code="5-2-01", display_name="학생 나")
        self.other_student = Student.objects.create(organization=self.other_school, classroom=self.other_class, student_code="5-1-01", display_name="학생 다")
        self.teacher = User.objects.create_user(username="teacher", email="teacher@example.test", password="test-password-123")
        self.parent = User.objects.create_user(username="parent", email="parent@example.test", password="test-password-123")
        self.school_admin = User.objects.create_user(username="school-admin", email="admin@example.test", password="test-password-123")
        TeacherAssignment.objects.create(classroom=self.class_a, user=self.teacher, created_by=self.school_admin)
        GuardianLink.objects.create(student=self.student_a, user=self.parent, verified_at=timezone.now())
        OrganizationAdministrator.objects.create(organization=self.school, user=self.school_admin)

    def test_teacher_sees_assigned_class_only(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.get("/api/v1/onclass/roster/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["student_id"] for row in response.data["students"]], [self.student_a.pk])

    def test_parent_sees_linked_child_only_and_cannot_start_whole_class(self):
        self.client.force_authenticate(self.parent)
        response = self.client.get("/api/v1/onclass/roster/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["student_id"] for row in response.data["students"]], [self.student_a.pk])
        response = self.client.post(f"/api/v1/onclass/classes/{self.class_a.pk}/sessions/", {}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_institution_admin_sees_all_classes_in_own_school_only(self):
        self.client.force_authenticate(self.school_admin)
        response = self.client.get("/api/v1/onclass/roster/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["student_id"] for row in response.data["students"]},
            {self.student_a.pk, self.student_b.pk},
        )

    @override_settings(ONCLASS_MASTER_EMAIL="owner@example.test")
    def test_master_scope_is_bound_to_one_configured_account(self):
        owner = User.objects.create_user(username="owner", email="owner@example.test", password="test-password-123")
        self.client.force_authenticate(owner)
        response = self.client.get("/api/v1/onclass/roster/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["students"]), 3)
        self.client.force_authenticate(self.school_admin)
        response = self.client.get("/api/v1/onclass/roster/")
        self.assertEqual({row["student_id"] for row in response.data["students"]}, {self.student_a.pk, self.student_b.pk})


class OnClassRemoteCommandTests(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="고산하늘초등학교", kind=Organization.Kind.SCHOOL)
        self.room = Classroom.objects.create(organization=self.org, name="5학년 1반", grade="5", room="1")
        self.teacher = User.objects.create_user(username="teacher", email="teacher@example.test", password="test-password-123")
        self.student = Student.objects.create(organization=self.org, classroom=self.room, student_code="5-1-01", display_name="학생 가")
        TeacherAssignment.objects.create(classroom=self.room, user=self.teacher, created_by=self.teacher)
        self.raw_device_token, token_hash = Device.issue_token()
        self.android = Device.objects.create(
            student=self.student,
            platform=Device.Platform.ANDROID,
            device_token_hash=token_hash,
            permission_granted=True,
            last_seen_at=timezone.now(),
        )
        self.device_client = APIClient()
        self.device_client.credentials(HTTP_X_ONCLASS_DEVICE_TOKEN=self.raw_device_token)
        self.client.force_authenticate(self.teacher)

    def test_session_start_waits_for_student_consent_before_creating_lock(self):
        response = self.client.post(f"/api/v1/onclass/classes/{self.room.pk}/sessions/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        session = ClassSession.objects.get(pk=response.data["session_id"])
        self.assertTrue(session.state == ClassSession.State.ACTIVE)
        self.assertEqual(self.android.commands.count(), 1)
        self.assertEqual(self.android.commands.first().action, RemoteCommand.Action.CONSENT)
        self.assertFalse(self.android.commands.filter(action=RemoteCommand.Action.LOCK).exists())

        poll = self.device_client.get("/api/v1/onclass/devices/commands/")
        self.assertEqual(poll.status_code, 200)
        consent_id = poll.data["commands"][0]["command_id"]
        result = self.device_client.post("/api/v1/onclass/devices/commands/", {
            "command_id": consent_id,
            "outcome": "accepted",
            "permission_granted": True,
        }, format="json")
        self.assertEqual(result.status_code, 200)
        lock = self.android.commands.get(action=RemoteCommand.Action.LOCK)
        self.assertEqual(lock.state, RemoteCommand.State.PENDING)

        poll = self.device_client.get("/api/v1/onclass/devices/commands/")
        lock_id = poll.data["commands"][0]["command_id"]
        result = self.device_client.post("/api/v1/onclass/devices/commands/", {
            "command_id": lock_id,
            "outcome": "applied",
            "permission_granted": True,
        }, format="json")
        self.assertEqual(result.status_code, 200)
        self.android.refresh_from_db()
        self.assertTrue(self.android.lock_active)
        roster = self.client.get("/api/v1/onclass/roster/")
        self.assertEqual(roster.data["students"][0]["state"], "locked")

    def test_decline_is_reported_separately_for_follow_up(self):
        response = self.client.post(f"/api/v1/onclass/classes/{self.room.pk}/sessions/", {}, format="json")
        poll = self.device_client.get("/api/v1/onclass/devices/commands/")
        result = self.device_client.post("/api/v1/onclass/devices/commands/", {
            "command_id": poll.data["commands"][0]["command_id"],
            "outcome": "declined",
        }, format="json")
        self.assertEqual(result.status_code, 200)
        roster = self.client.get("/api/v1/onclass/roster/")
        self.assertEqual(roster.data["students"][0]["state"], "consent_declined")
        self.assertFalse(self.android.commands.filter(action=RemoteCommand.Action.LOCK).exists())

    def test_ios_is_never_reported_as_locked_by_school_remote_command(self):
        ios_token, ios_hash = Device.issue_token()
        ios = Device.objects.create(
            student=self.student,
            platform=Device.Platform.IOS,
            device_token_hash=ios_hash,
            permission_granted=True,
            last_seen_at=timezone.now(),
        )
        response = self.client.post(f"/api/v1/onclass/classes/{self.room.pk}/sessions/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(ios.commands.exists())
        self.assertEqual(set(response.data["students"][0]["devices"]), {"consent_pending", "unsupported"})

    def test_expired_consent_cannot_create_late_lock(self):
        self.client.post(f"/api/v1/onclass/classes/{self.room.pk}/sessions/", {}, format="json")
        poll = self.device_client.get("/api/v1/onclass/devices/commands/")
        command_id = poll.data["commands"][0]["command_id"]
        command = self.android.commands.get(command_id=command_id)
        command.expires_at = timezone.now() - timedelta(seconds=1)
        command.save(update_fields=["expires_at"])
        result = self.device_client.post("/api/v1/onclass/devices/commands/", {
            "command_id": command_id,
            "outcome": "accepted",
            "permission_granted": True,
        }, format="json")
        self.assertEqual(result.status_code, 410)
        self.assertFalse(self.android.commands.filter(action=RemoteCommand.Action.LOCK).exists())

    def test_pairing_code_is_single_use_and_device_token_is_not_stored_raw(self):
        raw, code_hash = PairingCode.issue_code()
        PairingCode.objects.create(student=self.student, code_hash=code_hash, created_by=self.teacher, expires_at=timezone.now() + timedelta(minutes=15))
        anonymous = APIClient()
        response = anonymous.post("/api/v1/onclass/devices/enroll/", {"pairing_code": raw, "platform": "android"}, format="json")
        self.assertEqual(response.status_code, 201)
        token = response.data["device_token"]
        device = Device.objects.get(installation_id=response.data["device_id"])
        self.assertEqual(device.device_token_hash, digest_secret(token))
        second = anonymous.post("/api/v1/onclass/devices/enroll/", {"pairing_code": raw, "platform": "android"}, format="json")
        self.assertEqual(second.status_code, 400)

    def test_session_end_creates_unlock_only_for_confirmed_locked_devices(self):
        response = self.client.post(f"/api/v1/onclass/classes/{self.room.pk}/sessions/", {}, format="json")
        session_id = response.data["session_id"]
        poll = self.device_client.get("/api/v1/onclass/devices/commands/")
        self.device_client.post("/api/v1/onclass/devices/commands/", {
            "command_id": poll.data["commands"][0]["command_id"],
            "outcome": "accepted", "permission_granted": True,
        }, format="json")
        poll = self.device_client.get("/api/v1/onclass/devices/commands/")
        self.device_client.post("/api/v1/onclass/devices/commands/", {
            "command_id": poll.data["commands"][0]["command_id"],
            "outcome": "applied", "permission_granted": True,
        }, format="json")
        ended = self.client.post(f"/api/v1/onclass/sessions/{session_id}/end/", {}, format="json")
        self.assertEqual(ended.status_code, 200)
        unlock = self.android.commands.get(action=RemoteCommand.Action.UNLOCK)
        self.assertEqual(unlock.state, RemoteCommand.State.PENDING)
