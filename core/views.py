from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .forms import PatientRegistrationForm, DoctorRegistrationForm, AppointmentForm
from .models import Appointment
from .ml import get_risk_level, predict_no_show_risk
import random

def generate_captcha():
    """Generate a simple math CAPTCHA"""
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    # Only use addition to avoid negative numbers
    return {
        'question': f"What is {num1} + {num2}?",
        'answer': num1 + num2
    }

def login_view(request):
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Generate new CAPTCHA on GET request (first page load)
    if request.method == 'GET':
        captcha = generate_captcha()
        request.session['captcha_answer'] = captcha['answer']
        request.session['captcha_question'] = captcha['question']
        captcha_dict = captcha
    else:
        # On POST, retrieve existing CAPTCHA from session
        stored_answer = request.session.get('captcha_answer')
        stored_question = request.session.get('captcha_question', 'What is 5 + 3?')
        captcha_dict = {'question': stored_question, 'answer': stored_answer}
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        captcha_input = request.POST.get('captcha_answer')
        
        # Verify CAPTCHA - compare as integers
        stored_captcha = int(request.session.get('captcha_answer', 0))
        try:
            user_captcha = int(captcha_input) if captcha_input else 0
            if user_captcha != stored_captcha:
                messages.error(request, "Incorrect answer to the math problem. Please try again.")
                # Keep the same CAPTCHA for the form (don't regenerate)
                return render(request, 'core/login.html', {'captcha': captcha_dict})
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid number for the math problem.")
            return render(request, 'core/login.html', {'captcha': captcha_dict})
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful. Welcome back!")
            request.session.save()
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            # Keep the same CAPTCHA for the form (don't regenerate)
            return render(request, 'core/login.html', {'captcha': captcha_dict})
    
    return render(request, 'core/login.html', {'captcha': captcha_dict})

def register_patient(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Patient registration successful. Welcome to MediCare!')
            # Force session save before redirect
            request.session.save()
            return redirect('dashboard')
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard_view(request):
    user = request.user
    appointments = []
    
    if user.is_doctor:
        appointments = user.doctor_profile.appointments.all().order_by('date', 'time')
    elif user.is_patient:
        appointments = user.patient_profile.appointments.all().order_by('date', 'time')
    else:
        # Admin or staff maybe can see all
        appointments = Appointment.objects.all().order_by('date', 'time')

    appointment_risk_data = []
    for appointment in appointments:
        patient = appointment.patient
        patient_user = patient.user
        try:
            birth_year = patient.date_of_birth.year if patient.date_of_birth else patient_user.date_joined.year
            age = max(0, date.today().year - birth_year)
            risk_probability = predict_no_show_risk(
                age=age,
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
            appointment_risk_data.append({
                'appointment': appointment,
                'risk_probability': round(risk_probability, 3),
                'risk_level': get_risk_level(risk_probability),
            })
        except Exception:
            appointment_risk_data.append({
                'appointment': appointment,
                'risk_probability': None,
                'risk_level': 'Unavailable',
            })
        
    context = {
        'appointments': appointments,
        'total_appointments': appointments.count(),
        'upcoming_appointments': appointments.filter(appointment_type='Consultation', status__in=['Pending', 'Scheduled']).count(),
        'appointment_risk_data': appointment_risk_data,
    }
    return render(request, 'core/dashboard.html', context)

@staff_member_required
def add_doctor_view(request):
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor account created successfully!")
            return redirect('dashboard')
    else:
        form = DoctorRegistrationForm()
    
    return render(request, 'core/add_doctor.html', {'form': form})

@login_required
def book_appointment_view(request):
    if not request.user.is_patient:
        messages.error(request, "Only patients can book appointments.")
        return redirect('dashboard')

    prediction_context = None

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient_profile
            appointment.save()

            try:
                patient_profile = request.user.patient_profile
                birth_year = patient_profile.date_of_birth.year if patient_profile.date_of_birth else request.user.date_joined.year
                age = max(0, date.today().year - birth_year)
                risk_probability = predict_no_show_risk(
                    age=age,
                    gender="F" if request.user.first_name and request.user.first_name.lower().endswith('a') else "M",
                    neighbourhood=patient_profile.address.splitlines()[0] if patient_profile.address else "",
                    scholarship=False,
                    hypertension=False,
                    diabetes=False,
                    alcoholism=False,
                    handicap=0,
                    sms_received=False,
                    appointment_date=appointment.date,
                )
                prediction_context = {
                    'risk_probability': round(risk_probability, 3),
                    'risk_level': get_risk_level(risk_probability),
                }
            except Exception:
                prediction_context = {'risk_probability': None, 'risk_level': 'Unavailable'}

            messages.success(request, 'Appointment successfully booked!')
            return render(request, 'core/book_appointment.html', {'form': form, 'prediction': prediction_context})
    else:
        form = AppointmentForm()
        
    return render(request, 'core/book_appointment.html', {'form': form, 'prediction': prediction_context})

@login_required
def update_appointment_status(request, appt_id, action):
    appointment = get_object_or_404(Appointment, id=appt_id)
    
    if not request.user.is_doctor or request.user.doctor_profile != appointment.doctor:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
        
    if action == 'accept':
        appointment.status = 'Scheduled'
        appointment.save()
        messages.success(request, "Appointment accepted.")
        return redirect('dashboard')
        
    elif action == 'reject':
        if request.method == 'POST':
            reason = request.POST.get('rejection_reason', '')
            appointment.status = 'Rejected'
            appointment.rejection_reason = reason
            appointment.save()
            messages.success(request, "Appointment rejected.")
            return redirect('dashboard')
        return render(request, 'core/reject_appointment.html', {'appointment': appointment})

    return redirect('dashboard')


@staff_member_required
def api_patients_page(request):
    from .models import PatientProfile
    patients = PatientProfile.objects.select_related('user').all().order_by('user__last_name')
    patients_count = patients.count()
    # recent patients (simple heuristic: newest by pk)
    recent_count = patients.order_by('-id')[:5].count()
    return render(request, 'core/api_patients.html', {'patients': patients, 'patients_count': patients_count, 'recent_count': recent_count})


@staff_member_required
def api_doctors_page(request):
    from .models import DoctorProfile
    doctors = DoctorProfile.objects.select_related('user').all().order_by('user__last_name')
    doctors_count = doctors.count()
    return render(request, 'core/api_doctors.html', {'doctors': doctors, 'doctors_count': doctors_count})


@staff_member_required
def api_appointments_page(request):
    from .models import Appointment
    appointments = Appointment.objects.select_related('patient__user', 'doctor__user').all().order_by('-date', '-time')
    appointments_count = appointments.count()
    upcoming_count = appointments.filter(status__in=['Pending', 'Scheduled']).count()
    return render(request, 'core/api_appointments.html', {'appointments': appointments, 'appointments_count': appointments_count, 'upcoming_count': upcoming_count})
