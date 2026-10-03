from django.urls import path
from .views import (
    MobileCaptchaAPIView,
    MobileLoginAPIView,
    MobileRegisterAPIView,
    MobileUserAPIView,
    MobileDashboardAPIView,
    MobileAdminOverviewAPIView,
    MobileDoctorCreateAPIView,
    MobileAppointmentBookingAPIView,
    MobileAppointmentDecisionAPIView,
    PatientListCreateAPIView,
    PatientRetrieveUpdateDestroyAPIView,
    DoctorListCreateAPIView,
    DoctorRetrieveUpdateDestroyAPIView,
    AppointmentListCreateAPIView,
    AppointmentRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    path('auth/challenge/', MobileCaptchaAPIView.as_view(), name='api-mobile-challenge'),
    path('auth/login/', MobileLoginAPIView.as_view(), name='api-mobile-login'),
    path('auth/register/', MobileRegisterAPIView.as_view(), name='api-mobile-register'),
    path('auth/me/', MobileUserAPIView.as_view(), name='api-mobile-user'),
    path('mobile/dashboard/', MobileDashboardAPIView.as_view(), name='api-mobile-dashboard'),
    path('mobile/admin/', MobileAdminOverviewAPIView.as_view(), name='api-mobile-admin-overview'),
    path('mobile/admin/doctors/', MobileDoctorCreateAPIView.as_view(), name='api-mobile-doctor-create'),
    path('mobile/appointments/book/', MobileAppointmentBookingAPIView.as_view(), name='api-mobile-book-appointment'),
    path('mobile/appointments/<int:pk>/decision/', MobileAppointmentDecisionAPIView.as_view(), name='api-mobile-appointment-decision'),
    path('patients/', PatientListCreateAPIView.as_view(), name='api-patients'),
    path('patients/<int:pk>/', PatientRetrieveUpdateDestroyAPIView.as_view(), name='api-patient-detail'),

    path('doctors/', DoctorListCreateAPIView.as_view(), name='api-doctors'),
    path('doctors/<int:pk>/', DoctorRetrieveUpdateDestroyAPIView.as_view(), name='api-doctor-detail'),

    path('appointments/', AppointmentListCreateAPIView.as_view(), name='api-appointments'),
    path('appointments/<int:pk>/', AppointmentRetrieveUpdateDestroyAPIView.as_view(), name='api-appointment-detail'),
]
