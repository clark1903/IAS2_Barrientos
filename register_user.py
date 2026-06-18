import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insightedge.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
email = 'mcgbarrientos@tip.edu.ph'

user = User.objects.get(email=email)
user.set_password('@ClarkPogi2026')
user.save()

print("User password updated successfully.")
