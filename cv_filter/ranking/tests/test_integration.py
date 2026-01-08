"""
Integration tests for complete scoring engine.
"""

import unittest
from ranking.scoring.weighted_aggregator import WeightedScoringEngine, create_scoring_engine


class TestWeightedScoringEngine(unittest.TestCase):
    """Tests for the complete scoring engine."""
    
    def setUp(self):
        self.engine = create_scoring_engine()
    
    def test_complete_scoring(self):
        """Test scoring a complete candidate profile."""
        candidate_data = {
            'id': 'test-candidate-1',
            'skills': ['Python', 'Django', 'PostgreSQL', 'Docker', 'Git'],
            'experience_years': 5.0,
            'positions': [
                {'title': 'Backend Developer', 'years': 3},
                {'title': 'Python Developer', 'years': 2},
            ],
            'education_level': 'bachelor',
            'education_field': 'computer_science',
        }
        
        criteria = {
            'required_skills': ['Python', 'Django', 'PostgreSQL'],
            'preferred_skills': ['Docker', 'Redis'],
            'min_experience_years': 3,
            'ideal_experience_years': 7,
            'required_level': 'bachelor',
            'required_field': 'computer_science',
        }
        
        result = self.engine.score_candidate(candidate_data, criteria)
        
        # Verify structure
        self.assertIn('total_score', result)
        self.assertIn('component_scores', result)
        self.assertIn('explanation', result)
        self.assertIn('details', result)
        self.assertIn('quality', result)
        
        # Should be a strong match
        self.assertGreater(result['total_score'], 70)
        self.assertIn(result['quality'], ['excellent', 'strong', 'good'])
    
    def test_ranking_multiple_candidates(self):
        """Test ranking multiple candidates."""
        candidates = [
            {
                'id': 'candidate-1',
                'skills': ['Python', 'Django'],
                'experience_years': 3.0,
                'education_level': 'bachelor',
            },
            {
                'id': 'candidate-2',
                'skills': ['Python', 'Django', 'PostgreSQL', 'Docker'],
                'experience_years': 7.0,
                'education_level': 'master',
                'education_field': 'computer_science',
            },
            {
                'id': 'candidate-3',
                'skills': ['Java', 'Spring'],
                'experience_years': 5.0,
                'education_level': 'bachelor',
            },
        ]
        
        criteria = {
            'required_skills': ['Python', 'Django', 'PostgreSQL'],
            'min_experience_years': 3,
            'required_level': 'bachelor',
        }
        
        ranked = self.engine.rank_candidates(candidates, criteria)
        
        # Verify ranking
        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0]['rank'], 1)
        self.assertEqual(ranked[1]['rank'], 2)
        self.assertEqual(ranked[2]['rank'], 3)
        
        # Candidate 2 should be top ranked (more skills, more experience)
        self.assertEqual(ranked[0]['id'], 'candidate-2')
        
        # Scores should be descending
        self.assertGreaterEqual(ranked[0]['score'], ranked[1]['score'])
        self.assertGreaterEqual(ranked[1]['score'], ranked[2]['score'])
    
    def test_custom_weights(self):
        """Test scoring with custom weights."""
        candidate_data = {
            'skills': ['Python'],  # Only 1 skill
            'experience_years': 10.0,  # Lots of experience
            'education_level': 'master',
        }
        
        criteria = {
            'required_skills': ['Python', 'Django', 'PostgreSQL'],  # 3 required
            'min_experience_years': 3,
        }
        
        # Weight heavily towards experience
        weights_exp_heavy = {
            'skill_weight': 0.2,
            'experience_weight': 0.6,
            'education_weight': 0.2,
        }
        
        result_exp_heavy = self.engine.score_candidate(
            candidate_data, criteria, weights=weights_exp_heavy
        )
        
        # Weight heavily towards skills
        weights_skill_heavy = {
            'skill_weight': 0.7,
            'experience_weight': 0.2,
            'education_weight': 0.1,
        }
        
        result_skill_heavy = self.engine.score_candidate(
            candidate_data, criteria, weights=weights_skill_heavy
        )
        
        # Experience-heavy should score higher (good experience, poor skills)
        self.assertGreater(result_exp_heavy['total_score'], result_skill_heavy['total_score'])
    
    def test_poor_match(self):
        """Test scoring a poor match."""
        candidate_data = {
            'skills': ['Java', 'Spring'],  # Wrong stack
            'experience_years': 1.0,  # Too junior
            'education_level': 'high_school',
        }
        
        criteria = {
            'required_skills': ['Python', 'Django', 'PostgreSQL'],
            'min_experience_years': 5,
            'required_level': 'bachelor',
        }
        
        result = self.engine.score_candidate(candidate_data, criteria)
        
        # Should be a poor match
        self.assertLess(result['total_score'], 40)
        self.assertIn(result['quality'], ['poor', 'weak', 'fair'])
    
    def test_explanation_generation(self):
        """Test that explanations are generated."""
        candidate_data = {
            'skills': ['Python', 'Django'],
            'experience_years': 5.0,
            'education_level': 'bachelor',
        }
        
        criteria = {
            'required_skills': ['Python', 'Django'],
            'min_experience_years': 3,
        }
        
        result = self.engine.score_candidate(candidate_data, criteria)
        
        # Should have explanation
        self.assertTrue(result['explanation'])
        self.assertIsInstance(result['explanation'], str)
        self.assertGreater(len(result['explanation']), 50)


if __name__ == '__main__':
    unittest.main()
