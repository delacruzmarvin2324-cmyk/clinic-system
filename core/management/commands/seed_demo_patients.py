from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import PatientProfile


class Command(BaseCommand):
    help = "Create a few demo patients so the prediction system can be tested in the UI"

    def handle(self, *args, **options):
        User = get_user_model()
        patients = [
            {
                "username": "demo_patient_1",
                "first_name": "Maria",
                "last_name": "Lopez",
                "email": "maria@example.com",
                "password": "demo12345",
                "address": "JARDIM",
            },
            {
                "username": "demo_patient_2",
                "first_name": "John",
                "last_name": "Smith",
                "email": "john@example.com",
                "password": "demo12345",
                "address": "CENTRO",
            },
        ]

        for item in patients:
            user, created = User.objects.get_or_create(username=item["username"])
            if created:
                user.first_name = item["first_name"]
                user.last_name = item["last_name"]
                user.email = item["email"]
                user.is_patient = True
                user.set_password(item["password"])
                user.save()
                PatientProfile.objects.get_or_create(
                    user=user,
                    defaults={"address": item["address"]},
                )
                self.stdout.write(self.style.SUCCESS(f"Created {item['username']}"))
            else:
                self.stdout.write(f"Skipped existing {item['username']}")
