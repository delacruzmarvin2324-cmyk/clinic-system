import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction

from core.models import DoctorProfile


class Command(BaseCommand):
    help = 'Create the initial doctor from environment variables when configured.'

    fields = (
        'username',
        'password',
        'first_name',
        'last_name',
        'email',
        'specialty',
        'contact_number',
    )

    def _skip(self, message):
        self.stderr.write(self.style.WARNING(f'Initial doctor not provisioned: {message}'))

    def handle(self, *args, **options):
        values = {
            field: os.environ.get(f'INITIAL_DOCTOR_{field.upper()}', '')
            for field in self.fields
        }
        values = {
            field: value if field == 'password' else value.strip()
            for field, value in values.items()
        }

        if not any(value.strip() for value in values.values()):
            self.stdout.write('Initial doctor is not configured; skipping.')
            return

        missing = [field for field, value in values.items() if not value.strip()]
        if missing:
            names = ', '.join(f'INITIAL_DOCTOR_{field.upper()}' for field in missing)
            self._skip(f'missing settings: {names}')
            return

        try:
            validate_email(values['email'])
        except ValidationError as error:
            self._skip('INITIAL_DOCTOR_EMAIL must be a valid email address.')
            return

        User = get_user_model()
        existing_user = User.objects.filter(username=values['username']).first()
        if existing_user is not None:
            if not existing_user.is_doctor:
                self._skip('INITIAL_DOCTOR_USERNAME belongs to a non-doctor account.')
                return
            _, created = DoctorProfile.objects.get_or_create(
                user=existing_user,
                defaults={
                    'specialty': values['specialty'],
                    'contact_number': values['contact_number'],
                },
            )
            message = 'Initial doctor profile created.' if created else 'Initial doctor already exists; skipped.'
            self.stdout.write(message)
            return

        if User.objects.filter(email=values['email']).exists():
            self._skip('INITIAL_DOCTOR_EMAIL is already in use.')
            return

        user = User(
            username=values['username'],
            first_name=values['first_name'],
            last_name=values['last_name'],
            email=values['email'],
        )
        try:
            validate_password(values['password'], user=user)
        except ValidationError as error:
            self._skip('; '.join(error.messages))
            return

        with transaction.atomic():
            user = User.objects.create_user(
                username=values['username'],
                password=values['password'],
                first_name=values['first_name'],
                last_name=values['last_name'],
                email=values['email'],
                is_doctor=True,
            )
            DoctorProfile.objects.create(
                user=user,
                specialty=values['specialty'],
                contact_number=values['contact_number'],
            )

        self.stdout.write(self.style.SUCCESS('Initial doctor account created.'))