from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse


def role_required(*allowed_roles: str):
    """
    Enforce user authentication + role membership.
    Roles are stored in user.profile.role.
    """

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            # Treat superuser/staff as Admin for course projects.
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)

            role = getattr(getattr(request.user, "profile", None), "role", None)
            if role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, "You do not have permission to access that page.")
            return redirect(reverse("accounts:post_login"))

        return _wrapped

    return decorator

