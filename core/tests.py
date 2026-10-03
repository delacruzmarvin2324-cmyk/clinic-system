from datetime import date, time, timedelta
from io import StringIO
import os
from unittest.mock import patch

from django.core import signing
from django.core.management import call_command
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from .models import Appointment, DoctorProfile, PatientProfile, User
from .ml import get_risk_level, predict_no_show_risk, predict_no_show_risk_from_profile


class InitialDoctorProvisioningTests(APITestCase):
    settings = {
        'INITIAL_DOCTOR_USERNAME': 'initial_doctor',
        'INITIAL_DOCTOR_PASSWORD': 'Cobalt!River728_Sky',
        'INITIAL_DOCTOR_FIRST_NAME': 'Avery',
        'INITIAL_DOCTOR_LAST_NAME': 'Morgan',
        'INITIAL_DOCTOR_EMAIL': 'avery.morgan@example.test',
        'INITIAL_DOCTOR_SPECIALTY': 'Family medicine',
        'INITIAL_DOCTOR_CONTACT_NUMBER': '555-0100',
    }

    def test_creates_doctor_once_from_environment(self):
        output = StringIO()
        with patch.dict(os.environ, self.settings, clear=True):
            call_command('provision_initial_doctor', stdout=output)
            call_command('provision_initial_doctor', stdout=output)

        user = User.objects.get(username='initial_doctor')
        self.assertTrue(user.is_doctor)
        self.assertTrue(user.check_password(self.settings['INITIAL_DOCTOR_PASSWORD']))
        self.assertEqual(user.doctor_profile.specialty, 'Family medicine')
        self.assertEqual(User.objects.filter(username='initial_doctor').count(), 1)
        self.assertIn('already exists; skipped', output.getvalue())

        challenge = self.client.get('/api/auth/challenge/').data
        answer = signing.loads(
            challenge['challenge'], salt='mobile-login-captcha'
        )
        response = self.client.post('/api/auth/login/', {
            'username': 'initial_doctor',
            'password': self.settings['INITIAL_DOCTOR_PASSWORD'],
            'captcha_challenge': challenge['challenge'],
            'captcha_answer': str(answer),
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'doctor')

        doctors = self.client.get('/api/doctors/')
        self.assertEqual(doctors.status_code, 200)
        self.assertEqual(doctors.data[0]['specialty'], 'Family medicine')

        patient_response = self.client.post('/api/auth/register/', {
            'username': 'booking_patient',
            'password': 'Cedar_River_39!x',
            'first_name': 'Casey',
            'last_name': 'Taylor',
            'email': 'casey.taylor@example.test',
            'phone_number': '555-0101',
            'date_of_birth': '1990-04-12',
        }, format='json')
        self.assertEqual(patient_response.status_code, 201)

        booking = self.client.post('/api/mobile/appointments/book/', {
            'doctor_id': doctors.data[0]['id'],
            'appointment_type': 'Consultation',
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'time': '10:00',
        }, format='json', HTTP_AUTHORIZATION=f"Token {patient_response.data['token']}")
        self.assertEqual(booking.status_code, 201)

        challenge = self.client.get('/api/auth/challenge/').data
        answer = signing.loads(challenge['challenge'], salt='mobile-login-captcha')
        response = self.client.post('/api/auth/login/', {
            'username': 'initial_doctor',
            'password': self.settings['INITIAL_DOCTOR_PASSWORD'],
            'captcha_challenge': challenge['challenge'],
            'captcha_answer': str(answer),
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'doctor')

        doctor_headers = {'HTTP_AUTHORIZATION': f"Token {response.data['token']}"}
        dashboard = self.client.get('/api/mobile/dashboard/', **doctor_headers)
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.data['appointments'][0]['status'], 'Pending')

        decision = self.client.post(
            f"/api/mobile/appointments/{booking.data['id']}/decision/",
            {'action': 'accept'},
            format='json',
            **doctor_headers,
        )
        self.assertEqual(decision.status_code, 200)
        self.assertEqual(decision.data['status'], 'Scheduled')

        patient_dashboard = self.client.get(
            '/api/mobile/dashboard/',
            HTTP_AUTHORIZATION=f"Token {patient_response.data['token']}",
        )
        self.assertEqual(patient_dashboard.status_code, 200)
        self.assertEqual(patient_dashboard.data['appointments'][0]['status'], 'Scheduled')

    def test_partial_configuration_fails_clearly(self):
        output = StringIO()
        with patch.dict(os.environ, {'INITIAL_DOCTOR_USERNAME': 'initial_doctor'}, clear=True):
            call_command('provision_initial_doctor', stderr=output)

        self.assertIn('missing settings', output.getvalue())
        self.assertFalse(User.objects.filter(username='initial_doctor').exists())

    def test_invalid_doctor_settings_do_not_stop_provisioning_command(self):
        output = StringIO()
        invalid_settings = {
            **self.settings,
            'INITIAL_DOCTOR_EMAIL': 'not-an-email',
        }
        with patch.dict(os.environ, invalid_settings, clear=True):
            call_command('provision_initial_doctor', stderr=output)

        self.assertIn('valid email address', output.getvalue())
        self.assertFalse(User.objects.filter(username='initial_doctor').exists())

    def test_weak_password_does_not_stop_provisioning_command(self):
        output = StringIO()
        invalid_settings = {
            **self.settings,
            'INITIAL_DOCTOR_PASSWORD': 'password',
        }
        with patch.dict(os.environ, invalid_settings, clear=True):
            call_command('provision_initial_doctor', stderr=output)

        self.assertIn('password', output.getvalue().lower())
        self.assertFalse(User.objects.filter(username='initial_doctor').exists())


class AppointmentRiskPredictionTests(SimpleTestCase):
    def test_predict_no_show_risk_returns_a_probability(self):
        prediction = predict_no_show_risk(
            age=45,
            gender="F",
            neighbourhood="JARDIM",
            scholarship=False,
            hypertension=False,
            diabetes=False,
            alcoholism=False,
            handicap=0,
            sms_received=False,
            appointment_date=date.today() + timedelta(days=7),
        )

        self.assertIsInstance(prediction, float)
        self.assertGreaterEqual(prediction, 0.0)
        self.assertLessEqual(prediction, 1.0)

    def test_predict_no_show_risk_from_profile_uses_profile_values(self):
        prediction = predict_no_show_risk_from_profile(
            age=45,
            gender="F",
            neighbourhood="JARDIM",
            scholarship=True,
            hypertension=False,
            diabetes=False,
            alcoholism=False,
            handicap=0,
            sms_received=True,
            appointment_date=date.today() + timedelta(days=7),
        )

        self.assertIsInstance(prediction, float)
        self.assertGreaterEqual(prediction, 0.0)
        self.assertLessEqual(prediction, 1.0)

    def test_get_risk_level_labels_high_risk_correctly(self):
        self.assertEqual(get_risk_level(0.85), "High risk")
        self.assertEqual(get_risk_level(0.2), "Low risk")


class MobileApiTests(APITestCase):
    def test_future_scheduled_appointment_is_reported_as_upcoming(self):
        patient_user = User.objects.create_user('future_patient', password='Cedar_River_39!x', is_patient=True)
        patient = PatientProfile.objects.create(user=patient_user, date_of_birth=date(1990, 4, 12))
        doctor_user = User.objects.create_user('future_doctor', password='Cedar_River_39!x', is_doctor=True)
        doctor = DoctorProfile.objects.create(user=doctor_user, specialty='Family medicine')
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            status='Scheduled',
        )
        self.client.force_authenticate(user=patient_user)

        response = self.client.get('/api/mobile/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['appointments'][0]['status'], 'Scheduled')
        self.assertEqual(response.data['upcoming_appointments'], 1)

    def test_past_scheduled_appointment_is_reported_as_completed(self):
        patient_user = User.objects.create_user('past_patient', password='Cedar_River_39!x', is_patient=True)
        patient = PatientProfile.objects.create(user=patient_user, date_of_birth=date(1990, 4, 12))
        doctor_user = User.objects.create_user('past_doctor', password='Cedar_River_39!x', is_doctor=True)
        doctor = DoctorProfile.objects.create(user=doctor_user, specialty='Family medicine')
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=date.today() - timedelta(days=1),
            time=time(10, 0),
            status='Scheduled',
        )
        self.client.force_authenticate(user=patient_user)

        response = self.client.get('/api/mobile/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['appointments'][0]['status'], 'Completed')
        self.assertEqual(response.data['upcoming_appointments'], 0)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'Scheduled')

    def test_login_requires_a_valid_math_challenge(self):
        User.objects.create_user('captcha_patient', password='Cedar_River_39!x', is_patient=True)
        challenge = self.client.get('/api/auth/challenge/').data

        invalid = self.client.post('/api/auth/login/', {
            'username': 'captcha_patient',
            'password': 'Cedar_River_39!x',
            'captcha_challenge': challenge['challenge'],
            'captcha_answer': '0',
        }, format='json')
        self.assertEqual(invalid.status_code, 400)

        from django.core import signing

        answer = signing.loads(challenge['challenge'], salt='mobile-login-captcha')
        valid = self.client.post('/api/auth/login/', {
            'username': 'captcha_patient',
            'password': 'Cedar_River_39!x',
            'captcha_challenge': challenge['challenge'],
            'captcha_answer': str(answer),
        }, format='json')
        self.assertEqual(valid.status_code, 200)

    def test_patient_registration_returns_token_and_profile(self):
        response = self.client.post('/api/auth/register/', {
            'username': 'mobile_patient',
            'password': 'Cedar_River_39!x',
            'first_name': 'Morgan',
            'last_name': 'Lee',
            'email': 'morgan@example.com',
            'phone_number': '555-0100',
            'date_of_birth': '1990-04-12',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['role'], 'patient')
        self.assertTrue(PatientProfile.objects.filter(user__username='mobile_patient').exists())

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        current_user = self.client.get('/api/auth/me/')
        self.assertEqual(current_user.status_code, 200)
        self.assertEqual(current_user.data['user']['username'], 'mobile_patient')

    def test_patient_cannot_decide_doctor_appointment(self):
        patient_user = User.objects.create_user('mobile_patient_2', password='Cedar_River_39!x', is_patient=True)
        patient = PatientProfile.objects.create(user=patient_user, date_of_birth=date(1990, 4, 12))
        doctor_user = User.objects.create_user('mobile_doctor', password='Cedar_River_39!x', is_doctor=True)
        doctor = DoctorProfile.objects.create(user=doctor_user, specialty='Family medicine')
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
        )
        self.client.force_authenticate(user=patient_user)

        response = self.client.post(
            f'/api/mobile/appointments/{appointment.id}/decision/',
            {'action': 'accept'},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'Pending')
