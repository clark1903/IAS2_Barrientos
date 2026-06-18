import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insightedge.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()
email = 'maavanica@tip.edu.ph'
username = 'maavanica'
password = 'password123' # Defaulting to a safe dummy password

user, created = User.objects.get_or_create(
    username=username,
    defaults={'email': email}
)

if not created:
    user.email = email
    user.save()

# Set password only if created to avoid overriding if they already use it, 
# or we can set it explicitly. Let's set it to be sure they can login.
user.set_password(password)
user.save()

profile, p_created = Profile.objects.get_or_create(user=user)
profile.role = 'Professor'
profile.save()

if created:
    print(f"Created new user {email} with role Professor and password '{password}'")
else:
    print(f"Updated existing user {email} to have role Professor and reset password to '{password}'")
