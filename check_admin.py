import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insightedge.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.filter(username="admin").first()

if admin:
    print(f"Admin originally active: {admin.is_active}")
    admin.is_active = True
    admin.set_password("adminpassword123")
    admin.save()
    print("Admin reset to active with password 'adminpassword123'")
else:
    print("Admin does not exist")
