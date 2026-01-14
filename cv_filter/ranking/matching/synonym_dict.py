"""
Synonym dictionary for technical skills and keywords.
Maps common variations and abbreviations to canonical terms.
"""

from typing import List, Set

# Skill synonyms mapping
SKILL_SYNONYMS = {
    # Programming languages
    "javascript": ["js", "ecmascript", "es6", "es2015", "es2016", "es2017", "es2018", "es2019", "es2020"],
    "typescript": ["ts"],
    "python": ["python3", "py", "python2"],
    
    # Databases
    "postgresql": ["postgres", "psql", "pg"],
    "mongodb": ["mongo"],
    "mysql": ["my sql"],
    "sqlite": ["sqlite3"],
    
    # Frameworks - Backend
    "django": ["django rest framework", "drf"],
    "flask": [],
    "fastapi": ["fast api"],
    "express": ["expressjs", "express.js"],
    "nestjs": ["nest.js", "nest"],
    
    # Frameworks - Frontend
    "react": ["reactjs", "react.js"],
    "vue": ["vuejs", "vue.js"],
    "angular": ["angularjs", "angular.js"],
    "svelte": ["sveltejs"],
    "next": ["nextjs", "next.js"],
    
    # DevOps & Tools
    "docker": ["containerization", "docker-compose"],
    "kubernetes": ["k8s"],
    "jenkins": [],
    "git": ["github", "gitlab", "version control"],
    "ci/cd": ["continuous integration", "continuous deployment", "cicd"],
    
    # Cloud platforms
    "aws": ["amazon web services"],
    "gcp": ["google cloud platform", "google cloud"],
    "azure": ["microsoft azure"],
    
    # Web technologies
    "html": ["html5"],
    "css": ["css3"],
    "rest": ["rest api", "restful", "restful api"],
    "graphql": ["graph ql"],
    "websocket": ["websockets", "ws"],
    
    # Testing
    "pytest": ["py.test"],
    "jest": [],
    "mocha": [],
    "unittest": ["unit test", "unit testing"],
    
    # Data & ML
    "tensorflow": ["tf"],
    "pytorch": ["torch"],
    "pandas": [],
    "numpy": [],
    "scikit-learn": ["sklearn", "scikit learn"],
    
    # Other
    "api": ["apis"],
    "sql": ["structured query language"],
    "nosql": ["no sql"],
    "microservices": ["micro services", "microservice architecture"],
    "agile": ["scrum", "kanban"],
}


def get_synonyms(skill: str) -> Set[str]:
    """
    Get all synonyms for a given skill.

    Args:
        skill: Skill name to look up

    Returns:
        Set of synonyms including the original skill

    Examples:
        >>> get_synonyms("javascript")
        {'javascript', 'js', 'ecmascript', 'es6', ...}
        >>> get_synonyms("unknown")
        {'unknown'}
    """
    skill_lower = skill.lower().strip()
    
    # Check if skill is a canonical term
    if skill_lower in SKILL_SYNONYMS:
        return {skill_lower, *SKILL_SYNONYMS[skill_lower]}
    
    # Check if skill is a synonym of any canonical term
    for canonical, synonyms in SKILL_SYNONYMS.items():
        if skill_lower in synonyms:
            return {canonical, *synonyms}
    
    # No synonyms found, return just the skill itself
    return {skill_lower}


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill to its canonical form.

    Args:
        skill: Skill name to normalize

    Returns:
        Canonical skill name

    Examples:
        >>> normalize_skill("js")
        "javascript"
        >>> normalize_skill("Postgres")
        "postgresql"
        >>> normalize_skill("unknown")
        "unknown"
    """
    skill_lower = skill.lower().strip()
    
    # Already canonical
    if skill_lower in SKILL_SYNONYMS:
        return skill_lower
    
    # Find canonical form
    for canonical, synonyms in SKILL_SYNONYMS.items():
        if skill_lower in synonyms:
            return canonical
    
    # Return as-is if not found
    return skill_lower


def expand_skills(skills: List[str]) -> Set[str]:
    """
    Expand a list of skills to include all synonyms.

    Args:
        skills: List of skill names

    Returns:
        Set of skills including all synonyms

    Examples:
        >>> expand_skills(["Python", "JS"])
        {'python', 'python3', 'py', 'javascript', 'js', 'es6', ...}
    """
    expanded = set()
    
    for skill in skills:
        expanded.update(get_synonyms(skill))
    
    return expanded


def match_with_synonyms(skill: str, candidate_skills: List[str]) -> bool:
    """
    Check if a skill matches any candidate skill (including synonyms).

    Args:
        skill: Skill to look for
        candidate_skills: List of candidate's skills

    Returns:
        True if skill or any synonym matches a candidate skill

    Examples:
        >>> match_with_synonyms("JavaScript", ["Python", "JS", "React"])
        True
        >>> match_with_synonyms("PostgreSQL", ["MySQL", "MongoDB"])
        False
    """
    skill_synonyms = get_synonyms(skill)
    candidate_synonyms = expand_skills(candidate_skills)
    
    return bool(skill_synonyms & candidate_synonyms)
