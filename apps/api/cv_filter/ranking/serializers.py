from typing import Any, Dict, List, Optional

from rest_framework import serializers


class RankingCriteriaSerializer(serializers.Serializer):
    required_skills = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    preferred_skills = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    bonus_skills = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )

    min_experience_years = serializers.DecimalField(
        max_digits=4, decimal_places=1, required=False
    )
    ideal_experience_years = serializers.DecimalField(
        max_digits=4, decimal_places=1, required=False
    )

    target_role = serializers.CharField(required=False)
    relevant_titles = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )

    required_level = serializers.CharField(required=False)
    preferred_level = serializers.CharField(required=False)
    required_field = serializers.CharField(required=False)
    acceptable_fields = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )


class BiasConfigSerializer(serializers.Serializer):
    skill_weight = serializers.DecimalField(max_digits=3, decimal_places=2, default=0.50)
    experience_weight = serializers.DecimalField(max_digits=3, decimal_places=2, default=0.30)
    education_weight = serializers.DecimalField(max_digits=3, decimal_places=2, default=0.20)

    def validate(self, data):
        total = float(data.get("skill_weight", 0)) + float(data.get("experience_weight", 0)) + float(data.get("education_weight", 0))
        if total <= 0:
            raise serializers.ValidationError("Weights must sum to > 0")
        return data


class CandidateFiltersSerializer(serializers.Serializer):
    status = serializers.ListField(child=serializers.CharField(), required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=5000)


class RankingCreateSerializer(serializers.Serializer):
    criteria = RankingCriteriaSerializer()
    bias_config = BiasConfigSerializer(required=False)
    candidate_filters = CandidateFiltersSerializer(required=False)


class RankingRunSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(required=False, allow_null=True)


class CandidateScoreSerializer(serializers.Serializer):
    candidate_id = serializers.UUIDField()
    candidate_name = serializers.CharField(required=False)
    score = serializers.DecimalField(max_digits=6, decimal_places=2)
    rank = serializers.IntegerField()
    explanation = serializers.CharField(allow_blank=True)
    details_json = serializers.JSONField(required=False)


class RankingResultsSerializer(serializers.Serializer):
    run = RankingRunSerializer()
    results = CandidateScoreSerializer(many=True)
