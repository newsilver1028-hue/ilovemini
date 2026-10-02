import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create the first Django superuser from temporary environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        if not username and not password:
            self.stdout.write("Superuser bootstrap skipped (credentials not configured).")
            return
        if not username or not password:
            raise CommandError(
                "Set both DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD."
            )

        User = get_user_model()
        with transaction.atomic():
            existing = User.objects.filter(**{User.USERNAME_FIELD: username}).first()
            if existing:
                if not existing.is_superuser:
                    raise CommandError(
                        "The configured username already belongs to a non-superuser. "
                        "Choose a different DJANGO_SUPERUSER_USERNAME."
                    )
                self.stdout.write("Configured superuser already exists; no changes made.")
                return

            user = User(**{User.USERNAME_FIELD: username})
            if email and hasattr(user, "email"):
                user.email = email
            validate_password(password, user=user)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()

        self.stdout.write(self.style.SUCCESS("Initial Django superuser created."))
