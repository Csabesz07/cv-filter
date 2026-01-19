"""Local Natural Language Query parser for candidate search."""

import re
from typing import Dict, List, Optional


class LocalNLQParser:
    """Simple NLQ parser that works without external services."""
    
    # Skill keywords that commonly appear in queries
    TECH_SKILLS = {
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'r', 'scala',
        'react', 'vue', 'angular', 'django', 'flask', 'spring', 'node', 'nodejs', 'next.js', 'nextjs',
        'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes', 'elasticsearch',
        'aws', 'azure', 'gcp', 'git', 'jenkins', 'terraform',
        # Machine Learning & Data Science
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'xgboost', 'lightgbm',
        'pandas', 'numpy', 'spark', 'pyspark', 'tableau', 'powerbi', 'power bi',
        # Frontend
        'redux', 'tailwind', 'bootstrap', 'sass', 'webpack', 'vite',
        # Methodologies
        'machine learning', 'deep learning', 'nlp', 'computer vision', 'data science',
        'agile', 'scrum', 'devops', 'ci/cd'
    }
    
    # Language level patterns
    LANGUAGE_PATTERNS = {
        'en': {
            'must_have': r'\b(must have|required|necessar(?:y|ily)|essential)\b',
            'nice_to_have': r'\b(nice to have|preferred|optional|plus|bonus)\b',
            'years': r'(\d+)\s*(?:years?|yrs?)',
            'experience': r'\b(?:experience|exp)\b',
        },
        'hu': {
            'must_have': r'\b(?:kell|kötelező|szükséges|elvárás)\b',
            'nice_to_have': r'\b(?:előny|plusz|szeret(?:nénk|né)|jó lenne)\b',
            'years': r'(\d+)\s*(?:év(?:es|))',
            'experience': r'\b(?:tapasztalat|gyakorlat)\b',
        }
    }
    
    @classmethod
    def parse(cls, query: str, language: str = "hu") -> Dict:
        """
        Parse natural language query into structured filters.
        
        Args:
            query: Natural language search query
            language: Query language ('hu' or 'en')
            
        Returns:
            Dictionary with filters structure
        """
        query_lower = query.lower()
        
        filters = {
            "must_have_skills": [],
            "nice_to_have_skills": [],
            "min_years_experience": None,
            "keywords": [],
            "location": "",
            "remote": None,
        }
        
        # Extract years of experience
        years_pattern = cls.LANGUAGE_PATTERNS.get(language, cls.LANGUAGE_PATTERNS['en'])['years']
        years_match = re.search(years_pattern, query_lower)
        if years_match:
            filters["min_years_experience"] = int(years_match.group(1))
        
        # Extract tech skills
        must_have_pattern = cls.LANGUAGE_PATTERNS.get(language, cls.LANGUAGE_PATTERNS['en'])['must_have']
        nice_pattern = cls.LANGUAGE_PATTERNS.get(language, cls.LANGUAGE_PATTERNS['en'])['nice_to_have']
        
        # Find all potential tech skills in the query
        found_skills = []
        for skill in cls.TECH_SKILLS:
            if re.search(r'\b' + re.escape(skill) + r'\b', query_lower):
                found_skills.append(skill)
        
        # Additional common terms to extract as keywords
        words = re.findall(r'\b\w+\b', query_lower)
        
        # Categorize skills
        query_parts = query_lower.split()
        
        # Check context for must-have vs nice-to-have
        has_nice_marker = bool(re.search(nice_pattern, query_lower))
        has_must_marker = bool(re.search(must_have_pattern, query_lower))
        
        if found_skills:
            if has_nice_marker and not has_must_marker:
                filters["nice_to_have_skills"] = found_skills
            else:
                # Default to must_have
                filters["must_have_skills"] = found_skills
        
        # Extract role keywords (backend, frontend, etc.)
        role_keywords = {
            'backend', 'frontend', 'full-stack', 'fullstack', 'devops', 
            'data scientist', 'data engineer', 'machine learning', 'ml',
            'senior', 'junior', 'lead', 'architect',
            # Hungarian
            'fejlesztő', 'programozó', 'mérnök', 'vezető', 'szenior'
        }
        
        for keyword in role_keywords:
            if keyword in query_lower:
                filters["keywords"].append(keyword)
        
        # Add all skills as keywords too for vector search
        filters["keywords"].extend(found_skills)
        
        # Extract location if mentioned
        location_markers = {
            'en': r'\b(?:in|at|from|location:?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'hu': r'\b(?:(?:helyszín|lokáció):?\s+)?([A-Z][a-záéíóöőúüű]+(?:\s+[A-Z][a-záéíóöőúüű]+)*)'
        }
        location_pattern = location_markers.get(language, location_markers['en'])
        location_match = re.search(location_pattern, query)
        if location_match:
            filters["location"] = location_match.group(1)
        
        # Check for remote work
        if re.search(r'\b(?:remote|távmunka|home office)\b', query_lower):
            filters["remote"] = True
        
        return {"filters": filters}
