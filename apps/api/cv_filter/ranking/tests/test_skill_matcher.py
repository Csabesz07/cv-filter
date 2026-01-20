"""
Unit tests for skill matching functionality.
"""

import unittest
from ranking.scoring.skill_matcher import SkillMatcher
from ranking.matching.fuzzy_matcher import FuzzyMatcher
from ranking.matching.synonym_dict import get_synonyms, normalize_skill
from ranking.matching.skill_taxonomy import get_related_skills, implies_skill


class TestFuzzyMatcher(unittest.TestCase):
    """Tests for fuzzy string matching."""
    
    def setUp(self):
        self.matcher = FuzzyMatcher(threshold=85)
    
    def test_exact_match(self):
        """Test exact string matching."""
        self.assertTrue(self.matcher.match("Python", "Python"))
        self.assertTrue(self.matcher.match("python", "PYTHON"))
    
    def test_fuzzy_match(self):
        """Test fuzzy matching for similar strings."""
        self.assertTrue(self.matcher.match("PostgreSQL", "Postgres"))
        self.assertTrue(self.matcher.match("React.js", "ReactJS"))
    
    def test_no_match(self):
        """Test non-matching strings."""
        self.assertFalse(self.matcher.match("Python", "Java"))
        self.assertFalse(self.matcher.match("React", "Angular"))
    
    def test_similarity_score(self):
        """Test similarity scoring."""
        score = self.matcher.similarity("PostgreSQL", "Postgres")
        self.assertGreater(score, 80)
        
        score = self.matcher.similarity("Python", "Java")
        self.assertLess(score, 50)


class TestSynonymDict(unittest.TestCase):
    """Tests for synonym dictionary."""
    
    def test_get_synonyms(self):
        """Test synonym retrieval."""
        synonyms = get_synonyms("javascript")
        self.assertIn("js", synonyms)
        self.assertIn("javascript", synonyms)
    
    def test_normalize_skill(self):
        """Test skill normalization."""
        self.assertEqual(normalize_skill("JS"), "javascript")
        self.assertEqual(normalize_skill("Postgres"), "postgresql")
        self.assertEqual(normalize_skill("unknown_skill"), "unknown_skill")
    
    def test_synonym_matching(self):
        """Test that synonyms are recognized."""
        js_synonyms = get_synonyms("JavaScript")
        es6_synonyms = get_synonyms("ES6")
        self.assertTrue(js_synonyms & es6_synonyms)  # Should have intersection


class TestSkillTaxonomy(unittest.TestCase):
    """Tests for skill taxonomy and hierarchy."""
    
    def test_implies_skill(self):
        """Test hierarchical skill implication."""
        # Django implies Python
        self.assertTrue(implies_skill("django", "python"))
        # Python doesn't imply Django
        self.assertFalse(implies_skill("python", "django"))
    
    def test_related_skills(self):
        """Test related skills retrieval."""
        related = get_related_skills("django")
        self.assertIn("python", related)
        self.assertIn("flask", related)  # Sibling framework


class TestSkillMatcher(unittest.TestCase):
    """Tests for complete skill matching."""
    
    def setUp(self):
        self.matcher = SkillMatcher()
    
    def test_exact_match_scoring(self):
        """Test exact skill matching."""
        candidate_data = {
            'skills': ['Python', 'Django', 'PostgreSQL']
        }
        criteria = {
            'required_skills': ['Python', 'Django'],
        }
        
        result = self.matcher.calculate_score(candidate_data, criteria)
        
        self.assertGreater(result['score'], 0.9)
        self.assertEqual(len(result['matched']), 2)
    
    def test_partial_match(self):
        """Test partial skill matching."""
        candidate_data = {
            'skills': ['Python', 'Flask']
        }
        criteria = {
            'required_skills': ['Python', 'Django', 'PostgreSQL'],
        }
        
        result = self.matcher.calculate_score(candidate_data, criteria)
        
        # Should match 1 out of 3 required skills
        self.assertLess(result['score'], 0.5)
        self.assertGreater(result['score'], 0.0)
        self.assertIn('Python', result['matched'])
        self.assertIn('Django', result['missing'])
    
    def test_synonym_matching(self):
        """Test that synonyms are matched."""
        candidate_data = {
            'skills': ['JS', 'Postgres']
        }
        criteria = {
            'required_skills': ['JavaScript', 'PostgreSQL'],
        }
        
        result = self.matcher.calculate_score(candidate_data, criteria)
        
        # Synonyms should match
        self.assertGreater(result['score'], 0.9)
    
    def test_tiered_skills(self):
        """Test required, preferred, and bonus skills."""
        candidate_data = {
            'skills': ['Python', 'Django', 'Docker']
        }
        criteria = {
            'required_skills': ['Python', 'Django'],
            'preferred_skills': ['Docker', 'Kubernetes'],
            'bonus_skills': ['AWS'],
        }
        
        result = self.matcher.calculate_score(candidate_data, criteria)
        
        # Should have solid score (all required + 1 preferred)
        self.assertGreater(result['score'], 0.7)
        details = result['details']
        self.assertEqual(details['required_matched'], 2)
        self.assertEqual(details['preferred_matched'], 1)


if __name__ == '__main__':
    unittest.main()
