import secrets
from datetime import timedelta
from email.utils import formataddr

from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail, get_connection
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import FormView

from .forms import EmailAuthenticationForm, MFAVerificationForm
from .models import Profile


User = get_user_model()
PENDING_MFA_USER_ID = "pending_mfa_user_id"
PENDING_EMAIL_OTP_HASH = "pending_email_otp_hash"
PENDING_EMAIL_OTP_EXPIRES_AT = "pending_email_otp_expires_at"
OTP_VALID_MINUTES = 10


def _get_pending_mfa_user(request: HttpRequest):
    user_id = request.session.get(PENDING_MFA_USER_ID)
    if not user_id:
        return None
    try:
        return User.objects.select_related("profile").get(pk=user_id)
    except User.DoesNotExist:
        for key in (PENDING_MFA_USER_ID, PENDING_EMAIL_OTP_HASH, PENDING_EMAIL_OTP_EXPIRES_AT):
            request.session.pop(key, None)
        return None


def _complete_login(request: HttpRequest, user):
    login(request, user, backend="accounts.auth_backends.EmailBackend")
    for key in (PENDING_MFA_USER_ID, PENDING_EMAIL_OTP_HASH, PENDING_EMAIL_OTP_EXPIRES_AT):
        request.session.pop(key, None)
    return redirect("accounts:post_login")


def _send_email_otp(request: HttpRequest, user):
    code = f"{secrets.randbelow(1000000):06d}"
    request.session[PENDING_EMAIL_OTP_HASH] = make_password(code)
    request.session[PENDING_EMAIL_OTP_EXPIRES_AT] = int(
        (timezone.now() + timedelta(minutes=OTP_VALID_MINUTES)).timestamp()
    )
    from_email = formataddr((settings.EMAIL_FROM_NAME, settings.DEFAULT_FROM_EMAIL))

    if settings.DEBUG or not (settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD):
        connection = get_connection(backend='django.core.mail.backends.console.EmailBackend')
    else:
        connection = get_connection()

    send_mail(
        subject="Your InsightEdge verification code",
        message=(
            f"Your InsightEdge login verification code is {code}.\n\n"
            f"This code expires in {OTP_VALID_MINUTES} minutes."
        ),
        from_email=from_email,
        recipient_list=[user.email],
        fail_silently=False,
        connection=connection,
    )


def _otp_is_valid(request: HttpRequest, code: str) -> bool:
    otp_hash = request.session.get(PENDING_EMAIL_OTP_HASH, "")
    expires_at = request.session.get(PENDING_EMAIL_OTP_EXPIRES_AT)
    if not otp_hash or not expires_at:
        return False
    if timezone.now().timestamp() > expires_at:
        return False
    return check_password(code, otp_hash)


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = EmailAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:post_login")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        user = form.get_user()

        self.request.session[PENDING_MFA_USER_ID] = user.pk

        try:
            _send_email_otp(self.request, user)
        except Exception:
            for key in (PENDING_MFA_USER_ID, PENDING_EMAIL_OTP_HASH, PENDING_EMAIL_OTP_EXPIRES_AT):
                self.request.session.pop(key, None)
            messages.error(
                self.request,
                "We could not send the login verification code. Check your email settings and try again.",
            )
            return redirect("accounts:login")

        messages.info(self.request, f"A verification code has been sent to {user.email}.")
        return redirect("accounts:mfa_verify")


class LogoutView(auth_views.LogoutView):
    pass


class MFAVerifyView(FormView):
    template_name = "accounts/mfa_verify.html"
    form_class = MFAVerificationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:post_login")
        self.pending_user = _get_pending_mfa_user(request)
        if not self.pending_user:
            messages.error(request, "Please sign in again to continue.")
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["pending_user"] = self.pending_user
        ctx["otp_valid_minutes"] = OTP_VALID_MINUTES
        return ctx

    def form_valid(self, form):
        if not _otp_is_valid(self.request, form.cleaned_data["code"]):
            form.add_error("code", "That verification code is invalid or expired.")
            return self.form_invalid(form)
        return _complete_login(self.request, self.pending_user)


class MFAResendView(View):
    def post(self, request, *args, **kwargs):
        pending_user = _get_pending_mfa_user(request)
        if not pending_user:
            messages.error(request, "Please sign in again to request a new code.")
            return redirect("accounts:login")
        try:
            _send_email_otp(request, pending_user)
        except Exception:
            messages.error(
                request,
                "We could not resend the verification code. Check your email settings and try again.",
            )
            return redirect("accounts:mfa_verify")
        messages.success(request, f"A new verification code has been sent to {pending_user.email}.")
        return redirect("accounts:mfa_verify")


@login_required
def post_login_redirect(request):
    if request.user.is_superuser or request.user.is_staff:
        return redirect("dashboard:admin")

    role = getattr(getattr(request.user, "profile", None), "role", None)
    if role == Profile.Role.PROFESSOR:
        return redirect("dashboard:professor")
    if role == Profile.Role.COUNSELOR:
        return redirect("dashboard:counselor")
    if role == Profile.Role.ADMIN:
        return redirect("dashboard:admin")

    return redirect("dashboard:admin")


def home(request):
    if request.user.is_authenticated:
        return redirect("accounts:post_login")
    return render(request, "accounts/home.html")
