"""
Example usage of the ranking module.
Demonstrates how to use the scoring engine.
"""

from cv_filter.ranking.scoring.weighted_aggregator import create_scoring_engine


def example_basic_usage():
    """Basic usage example."""
    
    # Create scoring engine with default settings
    engine = create_scoring_engine()
    
    # Define candidate data
    candidate = {
        'id': 'candidate-123',
        'name': 'Nagy Péter',
        'skills': ['Python', 'Django', 'PostgreSQL', 'Docker', 'Git'],
        'experience_years': 5.5,
        'positions': [
            {'title': 'Backend Developer', 'years': 3},
            {'title': 'Python Developer', 'years': 2.5}
        ],
        'education_level': 'master',
        'education_field': 'computer_science',
    }
    
    # Define job criteria
    criteria = {
        'required_skills': ['Python', 'Django', 'REST API'],
        'preferred_skills': ['Docker', 'Kubernetes', 'Redis'],
        'bonus_skills': ['AWS', 'Terraform'],
        'min_experience_years': 3,
        'ideal_experience_years': 7,
        'target_role': 'Senior Backend Developer',
        'required_level': 'bachelor',
        'preferred_level': 'master',
        'required_field': 'computer_science',
    }
    
    # Score the candidate
    result = engine.score_candidate(candidate, criteria)
    
    # Print results
    print("=" * 60)
    print(f"Candidate: {candidate['name']}")
    print(f"Total Score: {result['total_score']:.1f}/100")
    print(f"Quality: {result['quality']}")
    print("=" * 60)
    print("\nComponent Scores:")
    print(f"  Skills:     {result['component_scores']['skills']*100:.0f}%")
    print(f"  Experience: {result['component_scores']['experience']*100:.0f}%")
    print(f"  Education:  {result['component_scores']['education']*100:.0f}%")
    print("\n" + "=" * 60)
    print("Explanation:")
    print(result['explanation'])
    print("=" * 60)


def example_ranking_multiple():
    """Example of ranking multiple candidates."""
    
    engine = create_scoring_engine()
    
    candidates = [
        {
            'id': '1',
            'name': 'Kovács Anna',
            'skills': ['Python', 'Django', 'PostgreSQL', 'Docker'],
            'experience_years': 7.0,
            'education_level': 'master',
            'education_field': 'computer_science',
        },
        {
            'id': '2',
            'name': 'Szabó Péter',
            'skills': ['Python', 'Flask', 'MySQL'],
            'experience_years': 3.0,
            'education_level': 'bachelor',
            'education_field': 'computer_science',
        },
        {
            'id': '3',
            'name': 'Kiss László',
            'skills': ['Python', 'Django', 'PostgreSQL', 'Redis', 'Docker', 'Kubernetes'],
            'experience_years': 10.0,
            'education_level': 'master',
            'education_field': 'software_engineering',
        },
    ]
    
    criteria = {
        'required_skills': ['Python', 'Django', 'PostgreSQL'],
        'preferred_skills': ['Docker', 'Redis'],
        'min_experience_years': 5,
        'required_level': 'bachelor',
    }
    
    # Rank all candidates
    ranked = engine.rank_candidates(candidates, criteria)
    
    # Print rankings
    print("\n" + "=" * 60)
    print("CANDIDATE RANKINGS")
    print("=" * 60)
    
    for candidate in ranked:
        print(f"\n#{candidate['rank']} - {candidate['name']}")
        print(f"   Score: {candidate['score']:.1f}/100 ({candidate['quality']})")
        print(f"   Skills: {candidate['component_scores']['skills']*100:.0f}% | "
              f"Experience: {candidate['component_scores']['experience']*100:.0f}% | "
              f"Education: {candidate['component_scores']['education']*100:.0f}%")
    
    print("\n" + "=" * 60)


def example_custom_weights():
    """Example with custom weight configuration."""
    
    # Create engine with skill-heavy weighting
    engine = create_scoring_engine(
        weights={
            'skill_weight': 0.70,      # 70% weight on skills
            'experience_weight': 0.20,  # 20% on experience
            'education_weight': 0.10,   # 10% on education
        }
    )
    
    candidate = {
        'skills': ['Python', 'Django', 'PostgreSQL', 'Docker', 'Kubernetes', 'AWS'],
        'experience_years': 2.0,  # Junior
        'education_level': 'bachelor',
    }
    
    criteria = {
        'required_skills': ['Python', 'Django', 'PostgreSQL', 'Docker'],
        'min_experience_years': 5,
        'required_level': 'bachelor',
    }
    
    result = engine.score_candidate(candidate, criteria)
    
    print("\n" + "=" * 60)
    print("CUSTOM WEIGHTS (Skill-Heavy)")
    print("=" * 60)
    print(f"Total Score: {result['total_score']:.1f}/100")
    print("\nWith skill-heavy weights, this junior candidate with strong")
    print("technical skills scores higher than with default weights.")
    print("=" * 60)


if __name__ == '__main__':
    print("\n### EXAMPLE 1: Basic Usage ###")
    example_basic_usage()
    
    print("\n\n### EXAMPLE 2: Ranking Multiple Candidates ###")
    example_ranking_multiple()
    
    print("\n\n### EXAMPLE 3: Custom Weights ###")
    example_custom_weights()
