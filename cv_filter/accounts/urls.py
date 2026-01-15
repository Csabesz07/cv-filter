from django.urls import path
from django.views.generic import RedirectView

from .views import (
    CVUploadView,
    CandidateListCreateView,
    CVFileListDeleteView,
    LoginPageView,
    LoginView,
    OrganizationListCreateView,
    OrganizationSelectView,
    RegisterPageView,
    RegisterView,
    AuditLogListView,
    CVAccessEventListView,
    RankingEventListView,
    UserMeView,
    NLQParseView,
    CandidateSearchView,
    CandidateSummaryView
)

urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),
    path('api/auth/register/', RegisterView.as_view(), name='api-register'),
    path('api/auth/login/', LoginView.as_view(), name='api-login'),
    path('api/auth/me/', UserMeView.as_view(), name='api-user-me'),
    path('api/orgs/', OrganizationListCreateView.as_view(), name='api-orgs'),
    path('api/orgs/select/', OrganizationSelectView.as_view(), name='api-org-select'),
    path('api/cv/upload/', CVUploadView.as_view(), name='api-cv-upload'),
    path('api/candidates/', CandidateListCreateView.as_view(), name='api-candidates'),
    path('api/cv/files/', CVFileListDeleteView.as_view(), name='api-cv-files'),
    path('api/cv/files/<uuid:cv_file_id>/', CVFileListDeleteView.as_view(), name='api-cv-file-detail'),
    path('api/audit/logs/', AuditLogListView.as_view(), name='api-audit-logs'),
    path('api/audit/events/', CVAccessEventListView.as_view(), name='api-cv-access-events'),
    path('api/audit/ranking/', RankingEventListView.as_view(), name='api-ranking-events'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('register/', RegisterPageView.as_view(), name='register'),
    path('api/nlq/parse/', NLQParseView.as_view(), name='api-nlq-parse'),
    path('api/candidates/search/', CandidateSearchView.as_view(), name='api-candidate-search'),
    path('api/candidates/<uuid:candidate_id>/summary/', CandidateSummaryView.as_view(), name='api-candidate-summary'),

]
