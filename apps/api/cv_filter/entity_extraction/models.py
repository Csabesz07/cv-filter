"""Data models for entity extraction."""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class ExtractedEntities:
    """Data class to store extracted entities from CV."""

    # Contact Information
    email: List[str]
    phone: List[str]
    linkedin: List[str]
    github: List[str]
    websites: List[str]

    # Technical Skills
    programming_languages: List[str]
    frameworks: List[str]
    databases: List[str]
    tools: List[str]
    cloud_platforms: List[str]

    # Soft Skills
    soft_skills: List[str]

    # Natural Languages
    languages: List[str]

    # Education
    degrees: List[str]
    certifications: List[str]

    # Experience
    job_titles: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict) -> "ExtractedEntities":
        """Create ExtractedEntities from dictionary."""
        # Get all expected fields with defaults to empty list
        return cls(
            email=data.get("email", []),
            phone=data.get("phone", []),
            linkedin=data.get("linkedin", []),
            github=data.get("github", []),
            websites=data.get("websites", []),
            programming_languages=data.get("programming_languages", []),
            frameworks=data.get("frameworks", []),
            databases=data.get("databases", []),
            tools=data.get("tools", []),
            cloud_platforms=data.get("cloud_platforms", []),
            soft_skills=data.get("soft_skills", []),
            languages=data.get("languages", []),
            degrees=data.get("degrees", []),
            certifications=data.get("certifications", []),
            job_titles=data.get("job_titles", []),
        )

    @classmethod
    def empty(cls) -> "ExtractedEntities":
        """Create an empty ExtractedEntities object."""
        return cls(
            email=[],
            phone=[],
            linkedin=[],
            github=[],
            websites=[],
            programming_languages=[],
            frameworks=[],
            databases=[],
            tools=[],
            cloud_platforms=[],
            soft_skills=[],
            languages=[],
            degrees=[],
            certifications=[],
            job_titles=[],
            projects=[],
            awards=[],
        )
