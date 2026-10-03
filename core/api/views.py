from datetime import date
from random import randint

from django.contrib.auth import authenticate
from django.core import signing
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.ml import get_risk_level, predict_no_show_risk
from core.models import PatientProfile, DoctorProfile, Appointment, User
from .serializers import PatientSerializer, DoctorSerializer, AppointmentSerializer


class MobileRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    date_of_birth = serializers.DateField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already in use.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password

        user = User(
            username=self.initial_data.get('username', ''),
            first_name=self.initial_data.get('first_name', ''),
            last_name=self.initial_data.get('last_name', ''),
            email=self.initial_data.get('email', ''),
        )
        validate_password(value, user=user)
        return value


class MobileLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            answer = int(request.data.get('captcha_answer', ''))
            expected_answer = signing.loads(
                request.data.get('captcha_challenge', ''),
                salt='mobile-login-captcha',
                max_age=300,
            )
        except (TypeError, ValueError, signing.BadSignature):
            return Response({'detail': 'The math challenge is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)
        if answer != expected_answer:
            return Response({'detail': 'Incorrect answer to the math problem.'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(
            request,
            username=request.data.get('username', ''),
            password=request.data.get('password', ''),
        )
        if user is None:
            return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': _mobile_user_payload(user)})


class MobileCaptchaAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        first = randint(1, 10)
        second = randint(1, 10)
        return Response({
            'question': f'What is {first} + {second}?',
            'challenge': signing.dumps(first + second, salt='mobile-login-captcha'),
        })


class MobileRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MobileRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=values['username'],
                password=values['password'],
                email=values['email'],
                first_name=values['first_name'],
                last_name=values['last_name'],
                is_patient=True,
            )
            profile = PatientProfile.objects.create(
                user=user,
                phone_number=values['phone_number'],
                date_of_birth=values['date_of_birth'],
            )
            token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'token': token.key, 'user': _mobile_user_payload(user, profile)},
            status=status.HTTP_201_CREATED,
        )


class MobileUserAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'user': _mobile_user_payload(request.user)})


class MobileDashboardAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_doctor:
            appointments = Appointment.objects.filter(doctor__user=user)
        elif user.is_patient:
            appointments = Appointment.objects.filter(patient__user=user)
        elif user.is_staff:
            appointments = Appointment.objects.all()
        else:
            return Response({'detail': 'This account has no clinic role.'}, status=status.HTTP_403_FORBIDDEN)

        appointments = appointments.select_related(
            'patient__user', 'doctor__user'
        ).order_by('date', 'time')
        results = [_mobile_appointment_payload(item) for item in appointments]
        upcoming = sum(
            item['appointment_type'] == 'Consultation'
            and item['status'] in ['Pending', 'Scheduled']
            and date.fromisoformat(item['date']) >= date.today()
            for item in results
        )
        return Response({
            'appointments': results,
            'total_appointments': len(results),
            'upcoming_appointments': upcoming,
        })


class MobileAdminOverviewAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        doctors = DoctorProfile.objects.select_related('user').order_by('user__last_name')
        patients = PatientProfile.objects.select_related('user').order_by('user__last_name')
        appointments = Appointment.objects.select_related(
            'patient__user', 'doctor__user'
        ).order_by('-date', '-time')
        return Response({
            'doctors': [{
                'id': doctor.id,
                'doctor_name': f'Dr. {doctor.user.first_name} {doctor.user.last_name}'.strip(),
                'specialty': doctor.specialty,
                'contact_number': doctor.contact_number,
            } for doctor in doctors],
            'patients': [{
                'id': patient.id,
                'name': f'{patient.user.first_name} {patient.user.last_name}'.strip(),
                'phone_number': patient.phone_number,
                'neighbourhood': patient.neighbourhood,
            } for patient in patients],
            'appointments': [_mobile_appointment_payload(item) for item in appointments],
        })


class MobileDoctorCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    specialty = serializers.CharField(max_length=100)
    contact_number = serializers.CharField(max_length=20)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already in use.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already in use.')
        return value

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password

        user = User(
            username=self.initial_data.get('username', ''),
            first_name=self.initial_data.get('first_name', ''),
            last_name=self.initial_data.get('last_name', ''),
            email=self.initial_data.get('email', ''),
        )
        validate_password(value, user=user)
        return value


class MobileDoctorCreateAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = MobileDoctorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        with transaction.atomic():
            user = User.objects.create_user(
                username=values['username'],
                password=values['password'],
                email=values['email'],
                first_name=values['first_name'],
                last_name=values['last_name'],
                is_doctor=True,
            )
            doctor = DoctorProfile.objects.create(
                user=user,
                specialty=values['specialty'],
                contact_number=values['contact_number'],
            )
        return Response({
            'id': doctor.id,
            'doctor_name': f'Dr. {user.first_name} {user.last_name}'.strip(),
            'specialty': doctor.specialty,
            'contact_number': doctor.contact_number,
        }, status=status.HTTP_201_CREATED)


class MobileAppointmentBookingSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    appointment_type = serializers.ChoiceField(choices=Appointment.TYPE_CHOICES)
    date = serializers.DateField()
    time = serializers.TimeField()
    notes = serializers.CharField(required=False, allow_blank=True)


class MobileAppointmentBookingAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_patient:
            return Response({'detail': 'Only patients can book appointments.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = MobileAppointmentBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        doctor = get_object_or_404(DoctorProfile, pk=values['doctor_id'])
        appointment = Appointment.objects.create(
            patient=request.user.patient_profile,
            doctor=doctor,
            appointment_type=values['appointment_type'],
            date=values['date'],
            time=values['time'],
            notes=values.get('notes', ''),
        )
        appointment = Appointment.objects.select_related(
            'patient__user', 'doctor__user'
        ).get(pk=appointment.pk)
        return Response(_mobile_appointment_payload(appointment), status=status.HTTP_201_CREATED)


class MobileAppointmentDecisionAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        appointment = get_object_or_404(
            Appointment.objects.select_related('doctor__user', 'patient__user'), pk=pk
        )
        if not request.user.is_doctor or appointment.doctor.user_id != request.user.id:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        action = request.data.get('action')
        if action == 'accept':
            appointment.status = 'Scheduled'
        elif action == 'reject':
            appointment.status = 'Rejected'
            appointment.rejection_reason = request.data.get('rejection_reason', '')
        else:
            return Response({'detail': 'Action must be accept or reject.'}, status=status.HTTP_400_BAD_REQUEST)
        appointment.save(update_fields=['status', 'rejection_reason'])
        return Response(_mobile_appointment_payload(appointment))


def _mobile_user_payload(user, patient_profile=None):
    if patient_profile is None and user.is_patient:
        patient_profile = getattr(user, 'patient_profile', None)
    if user.is_doctor:
        role = 'doctor'
    elif user.is_patient:
        role = 'patient'
    else:
        role = 'admin' if user.is_staff else 'unknown'
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': role,
        'patient_id': patient_profile.id if patient_profile else None,
    }


def _mobile_appointment_payload(appointment):
    patient = appointment.patient
    patient_user = patient.user
    doctor = appointment.doctor
    doctor_user = doctor.user
    try:
        birth_year = patient.date_of_birth.year if patient.date_of_birth else patient_user.date_joined.year
        probability = predict_no_show_risk(
            age=max(0, date.today().year - birth_year),
            gender=patient.gender,
            neighbourhood=patient.neighbourhood,
            scholarship=patient.scholarship,
            hypertension=patient.hypertension,
            diabetes=patient.diabetes,
            alcoholism=patient.alcoholism,
            handicap=patient.handicap,
            sms_received=patient.sms_received,
            appointment_date=appointment.date,
        )
        risk = {'risk_probability': round(probability, 3), 'risk_level': get_risk_level(probability)}
    except Exception:
        risk = {'risk_probability': None, 'risk_level': 'Unavailable'}
    effective_status = appointment.status
    if effective_status in ['Pending', 'Scheduled'] and appointment.date < date.today():
        effective_status = 'Completed'
    return {
        'id': appointment.id,
        'patient': f'{patient_user.first_name} {patient_user.last_name}'.strip(),
        'doctor': f'Dr. {doctor_user.first_name} {doctor_user.last_name}'.strip(),
        'doctor_id': doctor.id,
        'specialty': doctor.specialty,
        'appointment_type': appointment.appointment_type,
        'date': appointment.date.isoformat(),
        'time': appointment.time.strftime('%H:%M'),
        'status': effective_status,
        'notes': appointment.notes,
        'rejection_reason': appointment.rejection_reason,
        **risk,
    }


class PatientListCreateAPIView(generics.ListCreateAPIView):
    queryset = PatientProfile.objects.all()
    serializer_class = PatientSerializer


class PatientRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PatientProfile.objects.all()
    serializer_class = PatientSerializer


class DoctorListCreateAPIView(generics.ListCreateAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorSerializer


class DoctorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorSerializer


class AppointmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer


class AppointmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
