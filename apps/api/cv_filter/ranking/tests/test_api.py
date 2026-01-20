from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import Organization, User, Candidate


class RankingApiTests(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="TestOrg", slug="testorg")
        UserModel = get_user_model()
        self.user = UserModel.objects.create_user(
            username="tester",
            password="pass1234",
            organization=self.org,
        )
        self.client.force_authenticate(self.user)
        # Create minimal candidate
        Candidate.objects.create(
            organization=self.org,
            first_name="Anna",
            last_name="Kovacs",
            email="anna@example.com",
        )

    def test_ranking_create_and_results(self):
        create_url = reverse('api-ranking-create')
        payload = {
            "criteria": {
                "required_skills": ["Python"],
                "min_experience_years": 0
            }
        }
        resp = self.client.post(create_url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        run_id = resp.data['ranking_run_id']

        results_url = reverse('api-ranking-results', kwargs={'run_id': run_id})
        resp2 = self.client.get(results_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertIn('run', resp2.data)
        self.assertIn('results', resp2.data)
