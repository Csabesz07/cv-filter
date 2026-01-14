from django.urls import path
from django.views.generic import RedirectView

from .views import (
    CVUploadView,
    LoginPageView,
    LoginView,
    RegisterPageView,
    RegisterView,
    AuditLogListView,
    CVAccessEventListView,
)

urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),
    path('api/auth/register/', RegisterView.as_view(), name='api-register'),
    path('api/auth/login/', LoginView.as_view(), name='api-login'),
    path('api/cv/upload/', CVUploadView.as_view(), name='api-cv-upload'),
    path('api/audit/logs/', AuditLogListView.as_view(), name='api-audit-logs'),
    path('api/audit/events/', CVAccessEventListView.as_view(), name='api-cv-access-events'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('register/', RegisterPageView.as_view(), name='register'),
]
