"""
Skill taxonomy and hierarchical relationships.
Defines parent-child and related skill relationships.
"""

from typing import Dict, List, Set

# Hierarchical skill taxonomy
# Format: parent_skill -> [child_skills]
SKILL_HIERARCHY = {
    # Programming paradigms
    "backend": {
        "python": ["django", "flask", "fastapi", "celery", "sqlalchemy"],
        "javascript": ["nodejs", "express", "nestjs"],
        "java": ["spring", "spring boot", "hibernate"],
        "php": ["laravel", "symfony"],
        "ruby": ["rails", "ruby on rails"],
        "go": ["gin", "echo"],
    },
    
    "frontend": {
        "javascript": ["react", "vue", "angular", "svelte"],
        "html": ["html5"],
        "css": ["css3", "sass", "less", "tailwind"],
        "typescript": ["react", "vue", "angular"],
    },
    
    # Database skills
    "database": {
        "sql": ["postgresql", "mysql", "sqlite", "oracle", "mssql"],
        "nosql": ["mongodb", "redis", "cassandra", "dynamodb"],
        "orm": ["sqlalchemy", "django orm", "sequelize", "hibernate"],
    },
    
    # DevOps & Cloud
    "devops": {
        "containerization": ["docker", "kubernetes", "docker-compose"],
        "ci/cd": ["jenkins", "gitlab ci", "github actions", "travis ci"],
        "infrastructure": ["terraform", "ansible", "cloudformation"],
        "monitoring": ["prometheus", "grafana", "elk", "datadog"],
    },
    
    "cloud": {
        "aws": ["ec2", "s3", "lambda", "rds", "dynamodb"],
        "gcp": ["compute engine", "cloud storage", "cloud functions"],
        "azure": ["azure functions", "azure sql"],
    },
    
    # Testing
    "testing": {
        "python": ["pytest", "unittest", "nose"],
        "javascript": ["jest", "mocha", "jasmine", "cypress"],
        "unit testing": ["pytest", "jest", "junit"],
        "integration testing": ["selenium", "playwright", "cypress"],
    },
    
    # Data & AI
    "data science": {
        "python": ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch"],
        "machine learning": ["tensorflow", "pytorch", "scikit-learn", "keras"],
        "data visualization": ["matplotlib", "seaborn", "plotly"],
    },
}


def get_child_skills(skill: str, hierarchy: Dict = None) -> Set[str]:
    """
    Get all child skills for a parent skill.

    Args:
        skill: Parent skill name
        hierarchy: Optional custom hierarchy (uses SKILL_HIERARCHY by default)

    Returns:
        Set of child skills

    Examples:
        >>> get_child_skills("python")
        {'django', 'flask', 'fastapi', 'celery', 'sqlalchemy'}
    """
    if hierarchy is None:
        hierarchy = SKILL_HIERARCHY
    
    skill_lower = skill.lower().strip()
    children = set()
    
    # Search through all categories
    for category, skills_dict in hierarchy.items():
        if skill_lower in skills_dict:
            children.update(skills_dict[skill_lower])
        elif skill_lower == category:
            # If skill is a category, get all children
            for child_list in skills_dict.values():
                children.update(child_list)
    
    return children


def get_parent_skill(skill: str, hierarchy: Dict = None) -> Set[str]:
    """
    Get parent skills for a given skill.

    Args:
        skill: Child skill name
        hierarchy: Optional custom hierarchy

    Returns:
        Set of parent skills

    Examples:
        >>> get_parent_skill("django")
        {'python', 'backend'}
    """
    if hierarchy is None:
        hierarchy = SKILL_HIERARCHY
    
    skill_lower = skill.lower().strip()
    parents = set()
    
    # Search through all categories
    for category, skills_dict in hierarchy.items():
        for parent, children in skills_dict.items():
            if skill_lower in children:
                parents.add(parent)
                parents.add(category)  # Add category as well
    
    return parents


def get_related_skills(skill: str, hierarchy: Dict = None) -> Set[str]:
    """
    Get all related skills (children and siblings).

    Args:
        skill: Skill name
        hierarchy: Optional custom hierarchy

    Returns:
        Set of related skills

    Examples:
        >>> get_related_skills("django")
        {'python', 'flask', 'fastapi', 'celery', 'backend'}
    """
    if hierarchy is None:
        hierarchy = SKILL_HIERARCHY
    
    skill_lower = skill.lower().strip()
    related = set()
    
    # Get children
    related.update(get_child_skills(skill_lower, hierarchy))
    
    # Get parents
    parents = get_parent_skill(skill_lower, hierarchy)
    related.update(parents)
    
    # Get siblings (other children of same parents)
    for parent in parents:
        related.update(get_child_skills(parent, hierarchy))
    
    # Remove the skill itself
    related.discard(skill_lower)
    
    return related


def implies_skill(candidate_skill: str, required_skill: str, hierarchy: Dict = None) -> bool:
    """
    Check if having candidate_skill implies having required_skill.

    Args:
        candidate_skill: Skill candidate possesses
        required_skill: Skill being checked for
        hierarchy: Optional custom hierarchy

    Returns:
        True if candidate_skill implies required_skill

    Examples:
        >>> implies_skill("django", "python")
        True  # Knowing Django implies knowing Python
        >>> implies_skill("python", "django")
        False  # Knowing Python doesn't imply Django
    """
    if hierarchy is None:
        hierarchy = SKILL_HIERARCHY
    
    candidate_lower = candidate_skill.lower().strip()
    required_lower = required_skill.lower().strip()
    
    # Exact match
    if candidate_lower == required_lower:
        return True
    
    # Check if required_skill is a parent of candidate_skill
    parents = get_parent_skill(candidate_lower, hierarchy)
    return required_lower in parents


def calculate_skill_distance(skill1: str, skill2: str, hierarchy: Dict = None) -> int:
    """
    Calculate hierarchical distance between two skills.

    Args:
        skill1: First skill
        skill2: Second skill
        hierarchy: Optional custom hierarchy

    Returns:
        Distance (0 = same skill, 1 = parent-child, 2 = siblings, etc.)

    Examples:
        >>> calculate_skill_distance("django", "django")
        0
        >>> calculate_skill_distance("django", "python")
        1  # Direct parent-child
        >>> calculate_skill_distance("django", "flask")
        2  # Siblings under Python
    """
    if hierarchy is None:
        hierarchy = SKILL_HIERARCHY
    
    skill1_lower = skill1.lower().strip()
    skill2_lower = skill2.lower().strip()
    
    # Same skill
    if skill1_lower == skill2_lower:
        return 0
    
    # Direct parent-child relationship
    if skill2_lower in get_parent_skill(skill1_lower, hierarchy):
        return 1
    if skill1_lower in get_parent_skill(skill2_lower, hierarchy):
        return 1
    
    # Siblings (share common parent)
    parents1 = get_parent_skill(skill1_lower, hierarchy)
    parents2 = get_parent_skill(skill2_lower, hierarchy)
    if parents1 & parents2:  # Intersection
        return 2
    
    # Distant or unrelated
    return 3


def expand_skills_with_hierarchy(skills: List[str], include_parents: bool = True) -> Set[str]:
    """
    Expand skills list to include related skills from hierarchy.

    Args:
        skills: List of skills to expand
        include_parents: Whether to include parent skills

    Returns:
        Expanded set of skills

    Examples:
        >>> expand_skills_with_hierarchy(["django"], include_parents=True)
        {'django', 'python', 'backend'}
    """
    expanded = set(skill.lower() for skill in skills)
    
    for skill in skills:
        if include_parents:
            expanded.update(get_parent_skill(skill))
    
    return expanded
