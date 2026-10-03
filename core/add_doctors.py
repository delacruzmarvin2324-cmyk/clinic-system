import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_system.settings')
django.setup()

from core.models import User, DoctorProfile

def add_doctor():
    # Create doctor 1
    if not User.objects.filter(username='doctor1').exists():
        user1 = User.objects.create_user('doctor1', 'doc1@clinic.com', 'doctorpassword')
        user1.is_doctor = True
        user1.first_name = 'Sarah'
        user1.last_name = 'Dela Cruz'
        user1.save()
        
        DoctorProfile.objects.create(
            user=user1,
            specialty='Cardiology',
            contact_number='09239637204'
        )
        print("Doctor Sarah Dela Cruz added.")
        
    # Create doctor 2
    if not User.objects.filter(username='doctor2').exists():
        user2 = User.objects.create_user('doctor2', 'doc2@clinic.com', 'doctorpassword')    
        user2.is_doctor = True
        user2.first_name = 'Michael'
        user2.last_name = 'De Leon'
        user2.save()
        
        DoctorProfile.objects.create(
            user=user2,
            specialty='Neurology',
            contact_number='09105808667'
        )
        print("Doctor Michael De Leon added.")

if __name__ == '__main__':
    add_doctor()
