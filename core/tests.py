from datetime import date, time, timedelta

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from .models import Appointment, DoctorProfile, PatientProfile, User
from .ml import get_risk_level, predict_no_show_risk, predict_no_show_risk_from_profile


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
