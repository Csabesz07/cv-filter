from django.urls import path
from .views import RankingCreateView, RankingResultsView

urlpatterns = [
    path('create/', RankingCreateView.as_view(), name='api-ranking-create'),
    path('<uuid:run_id>/results/', RankingResultsView.as_view(), name='api-ranking-results'),
]
