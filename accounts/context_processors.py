def profile_role(request):
    role = None
    if getattr(request, "user", None) and request.user.is_authenticated:
        role = getattr(getattr(request.user, "profile", None), "role", None)
    return {"current_role": role}

