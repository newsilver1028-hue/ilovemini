from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, Q
from django.utils import timezone
from django.utils.dateparse import parse_date

from core.models import Reminder


class Command(BaseCommand):
    help = "Send one push notification for each incomplete reminder due on the selected date."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Target date in YYYY-MM-DD format (defaults to today in server timezone).")

    def handle(self, *args, **options):
        target_date = parse_date(options["date"]) if options["date"] else timezone.localdate()
        if target_date is None:
            raise CommandError("--date must use YYYY-MM-DD format.")

        reminders = Reminder.objects.filter(
            completed_at__isnull=True,
            notification_sent_at__isnull=True,
        ).filter(
            Q(due_date__lte=target_date)
            | Q(due_odometer_km__lte=F("vehicle__current_odometer_km"))
        ).filter(
            vehicle__ownerships__ended_at__isnull=True,
            vehicle__ownerships__user__isnull=False,
            created_at__gte=F("vehicle__ownerships__started_at"),
        ).select_related("vehicle").distinct()
        reminders = [
            reminder for reminder in reminders
            if reminder.vehicle.current_ownership
            and reminder.vehicle.current_ownership.user.push_devices.exists()
        ]
        if not reminders:
            self.stdout.write("No reminders due for registered devices.")
            return

        try:
            import firebase_admin
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app()
        except Exception as exc:
            raise CommandError(f"Firebase Admin is not configured: {exc}") from exc

        from core.push import send_reminder_notification

        sent = 0
        for reminder in reminders:
            try:
                mileage_reached = (
                    reminder.due_odometer_km is not None
                    and reminder.vehicle.current_odometer_km is not None
                    and reminder.vehicle.current_odometer_km >= reminder.due_odometer_km
                )
                date_due = reminder.due_date is not None and reminder.due_date <= target_date
                trigger = "date" if date_due else "odometer" if mileage_reached else "date"
                delivered = send_reminder_notification(reminder, trigger)
            except Exception as exc:
                raise CommandError(f"Failed to send reminder {reminder.pk}: {exc}") from exc
            if delivered:
                reminder.notification_sent_at = timezone.now()
                reminder.save(update_fields=["notification_sent_at"])
                sent += 1

        self.stdout.write(self.style.SUCCESS(f"Sent {sent} reminder notifications."))
