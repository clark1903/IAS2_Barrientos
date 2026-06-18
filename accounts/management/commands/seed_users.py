from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with default admin, professor, and counselor users.'

    def handle(self, *args, **kwargs):
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@tip.edu.ph',
                'password': 'admin@123',
                'first_name': 'System',
                'last_name': 'Admin',
                'role': Profile.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'professor',
                'email': 'professor@tip.edu.ph',
                'password': 'professor@123',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'role': Profile.Role.PROFESSOR,
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'counselor',
                'email': 'counselor@tip.edu.ph',
                'password': 'counselor@123',
                'first_name': 'John',
                'last_name': 'Smith',
                'role': Profile.Role.COUNSELOR,
                'is_staff': False,
                'is_superuser': False,
            }
        ]

        for data in users_data:
            role = data.pop('role')
            password = data.pop('password')
            try:
                user = User.objects.get(username=data['username'])
                updated_fields = []
                for field, value in data.items():
                    if getattr(user, field) != value:
                        setattr(user, field, value)
                        updated_fields.append(field)
                if not user.check_password(password):
                    user.set_password(password)
                    updated_fields.append('password')
                if not user.is_active:
                    user.is_active = True
                    updated_fields.append('is_active')
                if updated_fields:
                    save_fields = [field for field in updated_fields if field != 'password']
                    if 'password' in updated_fields:
                        save_fields.append('password')
                    user.save()
                profile = user.profile
                if profile.role != role:
                    profile.role = role
                    profile.save()
                self.stdout.write(self.style.SUCCESS(f'User "{user.username}" updated for email-based login.'))
            except User.DoesNotExist:
                user = User.objects.create_user(password=password, **data)
                
                # Update role
                profile = user.profile
                profile.role = role
                profile.save()
                user.is_active = True
                user.save(update_fields=["is_active"])
                
                self.stdout.write(self.style.SUCCESS(f'Successfully created user "{user.username}" with role {role}.'))
