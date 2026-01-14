import logging
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.models import RankingRun, RankingRunStatus
from accounts.logging_service import AuditLogService
from .serializers import (
    RankingCreateSerializer,
    RankingRunSerializer,
    RankingResultsSerializer,
)
from .services import RankingService

logger = logging.getLogger(__name__)
User = get_user_model()


class RankingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RankingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        criteria = serializer.validated_data["criteria"]
        bias_config = serializer.validated_data.get("bias_config")
        candidate_filters = serializer.validated_data.get("candidate_filters")

        org = request.user.organization
        if not org:
            return Response({"detail": "User has no organization"}, status=status.HTTP_403_FORBIDDEN)

        service = RankingService()
        try:
            run = service.start_and_execute_run(
                organization=org,
                created_by=request.user,
                criteria=criteria,
                bias_config=bias_config,
                candidate_filters=candidate_filters,
            )
            
            # Log ranking run creation
            AuditLogService.log(
                organization=org,
                event_type='ranking.created',
                entity_type='ranking_run',
                entity_id=run.id,
                actor_user=request.user,
                description=f'Ranking run created with {len(criteria)} criteria',
                metadata={
                    'criteria_count': len(criteria),
                    'has_bias_config': bias_config is not None,
                    'status': run.status,
                }
            )
            
        except Exception as e:
            logger.exception("Ranking run failed")
            
            # Log failure
            AuditLogService.log(
                organization=org,
                event_type='ranking.failed',
                entity_type='ranking_run',
                actor_user=request.user,
                description=f'Ranking run failed: {str(e)}',
                metadata={'error': str(e)}
            )
            
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = {
            "ranking_run_id": str(run.id),
            "status": run.status,
            "created_at": run.created_at,
        }
        return Response(response, status=status.HTTP_201_CREATED)


class RankingResultsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, run_id: str):
        # Validate run belongs to user's organization
        org = request.user.organization
        if not org:
            return Response({"detail": "User has no organization"}, status=status.HTTP_403_FORBIDDEN)

        try:
            run = RankingRun.objects.get(id=run_id, organization=org)
        except RankingRun.DoesNotExist:
            return Response({"detail": "Run not found"}, status=status.HTTP_404_NOT_FOUND)

        service = RankingService()
        results = service.fetch_results(run=run)

        payload = {
            "run": {
                "id": run.id,
                "status": run.status,
                "created_at": run.created_at,
                "completed_at": run.completed_at,
            },
            "results": results,
        }
        return Response(payload)
