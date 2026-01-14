from django.urls import path
from django.views.generic import RedirectView

from .views import (
    CVUploadView,
    LoginPageView,
    LoginView,
    OrganizationCreateView,
    RegisterPageView,
    RegisterView,
    AuditLogListView,
    CVAccessEventListView,
    RankingEventListView,
    UserMeView,
)

urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),
    path('api/auth/register/', RegisterView.as_view(), name='api-register'),
    path('api/auth/login/', LoginView.as_view(), name='api-login'),
    path('api/auth/me/', UserMeView.as_view(), name='api-user-me'),
    path('api/orgs/', OrganizationCreateView.as_view(), name='api-org-create'),
    path('api/cv/upload/', CVUploadView.as_view(), name='api-cv-upload'),
    path('api/audit/logs/', AuditLogListView.as_view(), name='api-audit-logs'),
    path('api/audit/events/', CVAccessEventListView.as_view(), name='api-cv-access-events'),
    path('api/audit/ranking/', RankingEventListView.as_view(), name='api-ranking-events'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('register/', RegisterPageView.as_view(), name='register'),
]
