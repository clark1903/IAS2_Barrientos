from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MFAResendView,
    MFAVerifyView,
    home,
    post_login_redirect,
)

app_name = "accounts"


urlpatterns = [
    path("", home, name="home"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("mfa/verify/", MFAVerifyView.as_view(), name="mfa_verify"),
    path("mfa/resend/", MFAResendView.as_view(), name="mfa_resend"),
    path("post-login/", post_login_redirect, name="post_login"),
]

