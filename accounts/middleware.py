from django.core.cache import cache
from django.http import HttpResponse

from .request_context import clear_request_context, set_request_context


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_request_context(getattr(request, "user", None), get_client_ip(request))
        try:
            return self.get_response(request)
        finally:
            clear_request_context()


class RateLimitMiddleware:
    LIMITS = {
        "/login/": (5, 300),
        "/mfa/verify/": (6, 300),
        "/mfa/resend/": (3, 300),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path in self.LIMITS:
            limit, window = self.LIMITS[request.path]
            ip_address = get_client_ip(request) or "unknown"
            cache_key = f"ratelimit:{request.path}:{ip_address}"
            current = cache.get(cache_key, 0)
            if current >= limit:
                response = HttpResponse(
                    "Too many requests. Please wait a few minutes and try again.",
                    status=429,
                )
                response["Retry-After"] = str(window)
                return response
            cache.set(cache_key, current + 1, timeout=window)
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """
    Add browser-facing defensive headers for the Django application.

    The policy allows the trusted CDNs used by the templates while keeping
    scripts, styles, fonts, images, frames, and form submissions scoped tightly.
    """

    CONTENT_SECURITY_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "base-uri 'self'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", self.CONTENT_SECURITY_POLICY)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.setdefault("Referrer-Policy", "same-origin")
        return response
