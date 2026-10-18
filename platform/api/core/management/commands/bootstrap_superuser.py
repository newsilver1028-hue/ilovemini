import base64
import binascii
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Create the configured administrator; optionally synchronize its password from the environment.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-password',
            action='store_true',
            help='Synchronize from DJANGO_SUPERUSER_PASSWORD_B64 or DJANGO_SUPERUSER_PASSWORD when the command runs.',
        )

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        encoded_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD_B64', '').strip()
        if encoded_password:
            try:
                password = base64.b64decode(encoded_password, validate=True).decode('utf-8')
            except (binascii.Error, UnicodeDecodeError):
                raise CommandError('DJANGO_SUPERUSER_PASSWORD_B64 must contain valid Base64-encoded UTF-8.')
        else:
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        if not username and not password:
            self.stdout.write('Superuser bootstrap skipped (credentials not configured).')
            return
        if not username or not password:
            raise CommandError('Set DJANGO_SUPERUSER_USERNAME and a password environment variable.')
        User = get_user_model()
        with transaction.atomic():
            user = User.objects.filter(**{User.USERNAME_FIELD: username}).first()
            if user:
                if not user.is_superuser:
                    raise CommandError('Username belongs to a non-superuser. Choose another username.')
                if options['sync_password'] and not user.check_password(password):
                    validate_password(password, user=user)
                    user.set_password(password)
                    user.save(update_fields=['password'])
                    self.stdout.write(self.style.SUCCESS('Configured superuser password synchronized.'))
                else:
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
