from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from reports.models import Intervention, Report
from students.models import AcademicRecord, Student

from .audit import log_audit_event, serialize_instance
from .models import Profile

User = get_user_model()
TRACKED_MODELS = (Student, AcademicRecord, Report, Intervention)


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, **kwargs):
    # In case users were created before installing this app.
    Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Profile)
def sync_profile_role_to_user(sender, instance: Profile, **kwargs):
    """
    Keep the Django `User.is_staff` flag in sync with `Profile.role`.

    - If a profile is set to `Profile.Role.ADMIN`, make the user `is_staff=True`
      so they can access the Django admin site.
    - Do not automatically grant `is_superuser`.
    """
    user = getattr(instance, "user", None)
    if not user:
        return

    should_be_staff = instance.role == Profile.Role.ADMIN
    if user.is_staff != should_be_staff:
        user.is_staff = should_be_staff
        user.save(update_fields=["is_staff"])


@receiver(pre_save)
def capture_previous_state(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    if instance.pk:
        try:
            instance._audit_before_state = serialize_instance(sender.objects.get(pk=instance.pk))
        except sender.DoesNotExist:
            instance._audit_before_state = {}
    else:
        instance._audit_before_state = {}


@receiver(post_save)
def audit_model_save(sender, instance, created, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    log_audit_event(
        action=f"{sender.__name__.lower()}.{'create' if created else 'update'}",
        instance=instance,
        before=getattr(instance, "_audit_before_state", {}),
        after=serialize_instance(instance),
    )


@receiver(post_delete)
def audit_model_delete(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    log_audit_event(
        action=f"{sender.__name__.lower()}.delete",
        model_name=instance._meta.label,
        object_pk=str(instance.pk),
        before=serialize_instance(instance),
        after={},
    )


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    log_audit_event(
        action="auth.login",
        model_name=user._meta.label,
        object_pk=str(user.pk),
        after={"email": user.email},
        user=user,
        ip_address=request.META.get("REMOTE_ADDR", ""),
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    if not user:
        return
    log_audit_event(
        action="auth.logout",
        model_name=user._meta.label,
        object_pk=str(user.pk),
        after={"email": user.email},
        user=user,
        ip_address=request.META.get("REMOTE_ADDR", "") if request else "",
    )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    attempted_username = credentials.get("username") or credentials.get("email") or ""
    log_audit_event(
        action="auth.login_failed",
        model_name=User._meta.label,
        object_pk="",
        after={"attempted_username": attempted_username},
        ip_address=request.META.get("REMOTE_ADDR", "") if request else "",
    )

