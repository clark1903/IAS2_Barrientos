from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from accounts.models import Profile

User = get_user_model()
TIP_EMAIL_DOMAIN = "@tip.edu.ph"


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control form-control-lg px-3 py-2",
                "placeholder": "Enter your @tip.edu.ph email",
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg px-3 py-2",
                "placeholder": "Enter password",
                "autocomplete": "current-password",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Please enter a valid @tip.edu.ph email address and password.",
        "inactive": "This account is inactive.",
    }

    def clean_username(self):
        email = self.cleaned_data["username"].strip().lower()
        if not email.endswith(TIP_EMAIL_DOMAIN):
            raise ValidationError("Only @tip.edu.ph email addresses can access this system.")
        return email

    def clean(self):
        email = self.cleaned_data.get("username", "").strip().lower()
        password = self.cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class MFAVerificationForm(forms.Form):
    code = forms.CharField(
        label="Authentication Code",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg px-3 py-2",
                "placeholder": "Enter 6-digit code",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
            }
        ),
    )

    def clean_code(self):
        code = self.cleaned_data["code"].strip().replace(" ", "")
        if not code.isdigit():
            raise ValidationError("Enter a valid 6-digit authentication code.")
        return code

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    role = forms.ChoiceField(
        choices=[(Profile.Role.PROFESSOR, 'Professor'), (Profile.Role.COUNSELOR, 'Counselor')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@tip.edu.ph'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if not email.endswith(TIP_EMAIL_DOMAIN):
            raise ValidationError("Only @tip.edu.ph email addresses can be used to access this system.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        # New accounts are inactive until admin approves
        user.is_active = False 
        
        if commit:
            user.save()
            
            # The signal will automatically create the profile, but we need to set the role.
            # However, if the signal runs before we can intercept it, we just update it.
            profile = user.profile
            profile.role = self.cleaned_data["role"]
            profile.save()
            
        return user
