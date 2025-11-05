from django.urls import path
from .views.auth import (
    RegisterClientView,
    RegisterAgentView,
    LoginView,
    RefreshView,
    LogoutView,
    MeView,
    OTPRequestView,
    OTPVerifyView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetFinalizeView,
)

urlpatterns = [
    path('auth/register/client', RegisterClientView.as_view()),
    path('auth/register/agent', RegisterAgentView.as_view()),
    path('auth/login', LoginView.as_view()),
    path('auth/refresh', RefreshView.as_view()),
    path('auth/logout', LogoutView.as_view()),
    path('auth/me', MeView.as_view()),
    path('auth/otp/request', OTPRequestView.as_view()),
    path('auth/otp/verify', OTPVerifyView.as_view()),
    path('auth/password/reset/request', PasswordResetRequestView.as_view()),
    path('auth/password/reset/verify', PasswordResetVerifyView.as_view()),
    path('auth/password/reset/finalize', PasswordResetFinalizeView.as_view()),
]

