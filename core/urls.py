from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add-doctor/', views.add_doctor_view, name='add_doctor'),
    path('book-appointment/', views.book_appointment_view, name='book_appointment'),
    path('appointment/<int:appt_id>/<str:action>/', views.update_appointment_status, name='update_appointment'),
    path('register/', views.register_patient, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('api-dashboard/patients/', views.api_patients_page, name='api_patients_page'),
    path('api-dashboard/doctors/', views.api_doctors_page, name='api_doctors_page'),
    path('api-dashboard/appointments/', views.api_appointments_page, name='api_appointments_page'),
]
