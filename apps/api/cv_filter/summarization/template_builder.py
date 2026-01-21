"""Template-based summary generation from extracted entities."""

import logging
from typing import List

try:
    from ..entity_extraction.models import ExtractedEntities
except ImportError:
    import sys
    from pathlib import Path

    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from entity_extraction.models import ExtractedEntities

logger = logging.getLogger(__name__)


class SummaryTemplateBuilder:
    """Builds CV summaries from extracted entities using templates."""

    @staticmethod
    def build_summary(entities: ExtractedEntities, language: str = "hu") -> str:
        """
        Build a 3-5 sentence summary from extracted entities.

        Args:
            entities: ExtractedEntities object containing all extracted data
            language: Language for the summary (default: "hu" for Hungarian)

        Returns:
            Summary text (3-5 sentences)
        """
        if language.lower() in ("hu", "hungarian"):
            return SummaryTemplateBuilder._build_hungarian_summary(entities)
        elif language.lower() in ("en", "english"):
            return SummaryTemplateBuilder._build_english_summary(entities)
        else:
            logger.warning(f"Unsupported language: {language}, defaulting to Hungarian")
            return SummaryTemplateBuilder._build_hungarian_summary(entities)

    @staticmethod
    def _build_english_summary(entities: ExtractedEntities) -> str:
        """Build English summary."""
        sentences = []

        # Sentence 1: Professional role/positions with seniority
        if entities.job_titles:
            primary_role = entities.job_titles[0].title()
            
            # Add seniority if available
            seniority_prefix = ""
            if hasattr(entities, 'seniority') and entities.seniority:
                seniority = entities.seniority[0].title() if isinstance(entities.seniority, list) else entities.seniority.title()
                if seniority.lower() not in ['junior', 'mid', 'senior', 'lead', 'staff']:
                    seniority_prefix = ""
                else:
                    seniority_prefix = f"{seniority} "
            
            # Add years of experience if available
            experience_suffix = ""
            if hasattr(entities, 'years_of_experience') and entities.years_of_experience and entities.years_of_experience > 0:
                experience_suffix = f" with {entities.years_of_experience}+ years of experience"
            
            sentence1 = f"The candidate is a {seniority_prefix}{primary_role}{experience_suffix}."
            
            # Add additional roles if available
            if len(entities.job_titles) > 1:
                additional_roles = [t.title() for t in entities.job_titles[1:3]]
                sentence1 = (
                    f"The candidate is a {seniority_prefix}{primary_role}{experience_suffix}, "
                    f"with additional expertise as {SummaryTemplateBuilder._join_with_and(additional_roles)}."
                )
            sentences.append(sentence1)

        # Sentence 2: Technical skills with focus on primary expertise
        skill_components = []
        
        # Programming languages (top 3-4 most important)
        if entities.programming_languages:
            langs = [lang.title() for lang in entities.programming_languages[:4]]
            skill_components.append(f"specializes in {SummaryTemplateBuilder._join_with_and(langs)}")
        
        # Frameworks/technologies (top 2-3)
        if entities.frameworks:
            frameworks = [fw.title() for fw in entities.frameworks[:3]]
            skill_components.append(f"works with {SummaryTemplateBuilder._join_with_and(frameworks)}")

        if skill_components:
            sentence2 = f"The candidate {' and '.join(skill_components[:2])}."
            sentences.append(sentence2)

        # Sentence 3: Infrastructure and tooling expertise
        infra_parts = []
        
        if entities.tools:
            tools = [tool.title() for tool in entities.tools[:3]]
            infra_parts.append(f"experienced with {SummaryTemplateBuilder._join_with_and(tools)}")
        
        if entities.cloud_platforms:
            clouds = [c.upper() if c.lower() in ['aws', 'gcp', 'azure'] else c.title() for c in entities.cloud_platforms[:2]]
            infra_parts.append(f"proficient in {SummaryTemplateBuilder._join_with_and(clouds)}")
        
        if entities.databases:
            dbs = [db.upper() if len(db) <= 5 else db.title() for db in entities.databases[:2]]
            infra_parts.append(f"works with {SummaryTemplateBuilder._join_with_and(dbs)}")

        if infra_parts:
            sentence3 = f"Technical stack includes {', '.join(infra_parts[:2])}."
            sentences.append(sentence3)

        # Sentence 4: Education and certifications
        qual_parts = []
        
        if entities.degrees:
            # Filter out incomplete/invalid degrees
            valid_degrees = [d.title() for d in entities.degrees[:2] if d and len(d) > 2]
            if valid_degrees:
                qual_parts.append(f"holds a {SummaryTemplateBuilder._join_with_and(valid_degrees)} degree")
        
        if entities.certifications:
            # Filter out incomplete certifications and fix common issues
            valid_certs = []
            for cert in entities.certifications[:2]:
                if cert and len(cert) > 2:
                    # Skip incomplete certifications like "Ng"
                    cert_clean = cert.strip()
                    if len(cert_clean) <= 3 and not cert_clean.isupper():
                        continue
                    valid_certs.append(cert.title())
            
            if valid_certs:
                qual_parts.append(f"certified in {SummaryTemplateBuilder._join_with_and(valid_certs)}")

        if qual_parts:
            sentence4 = f"The candidate {SummaryTemplateBuilder._join_with_and(qual_parts)}."
            sentences.append(sentence4)

        # Sentence 5: Languages and soft skills
        additional_info = []
        
        if entities.languages and len(entities.languages) > 0:
            # Filter out invalid language entries
            valid_langs = [lang.title() for lang in entities.languages[:3] if lang and len(lang) > 1]
            if valid_langs:
                if len(valid_langs) == 1:
                    additional_info.append(f"fluent in {valid_langs[0]}")
                else:
                    additional_info.append(f"speaks {SummaryTemplateBuilder._join_with_and(valid_langs)}")
        
        if entities.soft_skills and len(sentences) < 4:
            soft = [s.lower() for s in entities.soft_skills[:2]]
            if soft:
                additional_info.append(f"demonstrates strong {SummaryTemplateBuilder._join_with_and(soft)} skills")

        if additional_info and len(sentences) < 5:
            sentence5 = f"The candidate {SummaryTemplateBuilder._join_with_and(additional_info[:2])}."
            sentences.append(sentence5)

        # Ensure we have at least 3 sentences
        if len(sentences) < 3:
            sentences.append("The candidate has relevant professional experience.")

        # Join sentences (ensure max 5 sentences)
        summary = " ".join(sentences[:5])

        logger.debug(f"Generated English summary with {len(sentences)} sentences")
        return summary

    @staticmethod
    def _build_hungarian_summary(entities: ExtractedEntities) -> str:
        """Build Hungarian summary."""
        sentences = []

        # Sentence 1: Professional role/positions with seniority
        if entities.job_titles:
            primary_role = entities.job_titles[0].title()
            
            # Add seniority if available
            seniority_prefix = ""
            if hasattr(entities, 'seniority') and entities.seniority:
                seniority = entities.seniority[0].title() if isinstance(entities.seniority, list) else entities.seniority.title()
                seniority_map = {
                    'junior': 'Junior',
                    'mid': 'Középhaladó',
                    'senior': 'Senior',
                    'lead': 'Vezető',
                    'staff': 'Senior'
                }
                seniority_prefix = seniority_map.get(seniority.lower(), "") + " " if seniority.lower() in seniority_map else ""
            
            # Add years of experience
            experience_suffix = ""
            if hasattr(entities, 'years_of_experience') and entities.years_of_experience and entities.years_of_experience > 0:
                experience_suffix = f", {entities.years_of_experience}+ év tapasztalattal"
            
            sentence1 = f"A jelölt {seniority_prefix}{primary_role}{experience_suffix}."
            
            # Add additional roles
            if len(entities.job_titles) > 1:
                additional_roles = [t.title() for t in entities.job_titles[1:3]]
                sentence1 = (
                    f"A jelölt {seniority_prefix}{primary_role}{experience_suffix}, "
                    f"szaktudással rendelkezik {SummaryTemplateBuilder._join_with_and_hu(additional_roles)} területén is."
                )
            sentences.append(sentence1)

        # Sentence 2: Technical skills (programming languages and frameworks)
        technical_skills_parts = []
        if entities.programming_languages:
            langs = entities.programming_languages[:5]
            technical_skills_parts.append(
                f"jól ért a következő programozási nyelvekhez: "
                f"{', '.join(lang.title() for lang in langs)}"
            )
        if entities.frameworks:
            frameworks = entities.frameworks[:3]
            technical_skills_parts.append(
                f"tapasztalt a következő keretrendszerekkel: "
                f"{', '.join(fw.title() for fw in frameworks)}"
            )
        if entities.databases:
            dbs = entities.databases[:3]
            technical_skills_parts.append(
                f"ismeri a következő adatbázisokat: "
                f"{', '.join(db.title() for db in dbs)}"
            )

        if technical_skills_parts:
            sentence2 = f"A jelölt {', '.join(technical_skills_parts[:2])}."
            sentences.append(sentence2)

        # Sentence 3: Additional technical skills (tools, cloud platforms)
        additional_skills = []
        if entities.tools:
            tools = entities.tools[:3]
            additional_skills.append(
                f"eszközök, mint például {', '.join(tool.title() for tool in tools)}"
            )
        if entities.cloud_platforms:
            clouds = entities.cloud_platforms[:2]
            additional_skills.append(
                f"felhő platformok, mint például {', '.join(c.title() for c in clouds)}"
            )

        if additional_skills:
            sentence3 = f"A jelölt tapasztalattal rendelkezik {', '.join(additional_skills)} használatában."
            sentences.append(sentence3)

        # Sentence 4: Qualifications (education and certifications)
        qual_parts = []
        
        if entities.degrees:
            # Filter out incomplete/invalid degrees
            valid_degrees = [d.title() for d in entities.degrees[:2] if d and len(d) > 2]
            if valid_degrees:
                qual_parts.append(f"{SummaryTemplateBuilder._join_with_and_hu(valid_degrees)} végzettséggel rendelkezik")
        
        if entities.certifications:
            # Filter out incomplete certifications
            valid_certs = []
            for cert in entities.certifications[:2]:
                if cert and len(cert) > 2:
                    cert_clean = cert.strip()
                    if len(cert_clean) <= 3 and not cert_clean.isupper():
                        continue
                    valid_certs.append(cert.title())
            
            if valid_certs:
                qual_parts.append(f"{SummaryTemplateBuilder._join_with_and_hu(valid_certs)} tanúsítvánnyal rendelkezik")

        if qual_parts:
            sentence4 = f"A jelölt {SummaryTemplateBuilder._join_with_and_hu(qual_parts)}."
            sentences.append(sentence4)

        # Sentence 5: Soft skills and languages (if available)
        additional_info = []
        if entities.soft_skills:
            soft = entities.soft_skills[:3]
            additional_info.append(
                f"részletes {', '.join(s.title() for s in soft)} készségekkel rendelkezik"
            )
        if entities.languages:
            langs = entities.languages[:3]
            additional_info.append(
                f"a következő nyelveken kommunikál: "
                f"{', '.join(lang.title() for lang in langs)}"
            )

        if additional_info and len(sentences) < 5:
            sentence5 = f"A jelölt {additional_info[0]}."
            sentences.append(sentence5)

        # Join sentences (ensure max 5 sentences)
        summary = " ".join(sentences[:5])

        logger.debug(f"Generated Hungarian summary with {len(sentences)} sentences")
        return summary

    @staticmethod
    def _format_list(items: List[str], max_items: int = 5) -> str:
        """
        Format a list of items for inclusion in summary.

        Args:
            items: List of items to format
            max_items: Maximum number of items to include

        Returns:
            Formatted string
        """
        if not items:
            return ""
        limited = items[:max_items]
        if len(items) > max_items:
            return f"{', '.join(limited)}, and others"
        elif len(limited) > 1:
            return f"{', '.join(limited[:-1])}, and {limited[-1]}"
        else:
            return limited[0]

    @staticmethod
    def _join_with_and(items: List[str]) -> str:
        """
        Join a list of items with commas and 'and'.
        
        Args:
            items: List of items to join
            
        Returns:
            Formatted string (e.g., "A, B, and C" or "A and B" or "A")
        """
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return f"{', '.join(items[:-1])}, and {items[-1]}"

    @staticmethod
    def _join_with_and_hu(items: List[str]) -> str:
        """
        Join a list of items with commas and 'és' (Hungarian).
        
        Args:
            items: List of items to join
            
        Returns:
            Formatted string (e.g., "A, B és C" or "A és B" or "A")
        """
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} és {items[1]}"
        return f"{', '.join(items[:-1])} és {items[-1]}"
