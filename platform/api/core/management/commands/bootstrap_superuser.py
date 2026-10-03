import os
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Create the initial administrator from environment variables, without changing an existing password.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if not username and not password:
            self.stdout.write('Superuser bootstrap skipped (credentials not configured).')
            return
        if not username or not password:
            raise CommandError('Set both DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD.')
        User = get_user_model()
        with transaction.atomic():
            user = User.objects.filter(**{User.USERNAME_FIELD: username}).first()
            if user:
                if not user.is_superuser:
                    raise CommandError('Username belongs to a non-superuser. Choose another username.')
                self.stdout.write('Configured superuser already exists; no changes made.')
                return
            user = User(**{User.USERNAME_FIELD: username})
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
            if email and hasattr(user, 'email'):
                user.email = email
            validate_password(password, user=user)
            user.is_staff = user.is_superuser = user.is_active = True
            user.set_password(password)
            user.save()
        self.stdout.write(self.style.SUCCESS('Initial Django superuser created.'))
