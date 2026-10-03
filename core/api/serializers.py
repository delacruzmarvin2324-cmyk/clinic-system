from rest_framework import serializers
from core.models import PatientProfile, DoctorProfile, Appointment, User


class PatientSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    user_full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'user_full_name', 'phone_number', 'date_of_birth', 'address', 
                  'gender', 'hypertension', 'diabetes', 'alcoholism', 'handicap', 'scholarship', 
                  'sms_received', 'neighbourhood']

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'doctor_name', 'specialty', 'contact_number']

    def get_doctor_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"


class AppointmentSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField(read_only=True)
    doctor = serializers.SerializerMethodField(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(queryset=PatientProfile.objects.all(), write_only=True, source='patient')
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=DoctorProfile.objects.all(), write_only=True, source='doctor')

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'patient_id', 'doctor_id', 'appointment_type', 'date', 'time', 'status', 'notes', 'rejection_reason']

    def get_patient(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}"

    def get_doctor(self, obj):
        return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}"
