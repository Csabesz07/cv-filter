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

        # Sentence 1: Professional role/positions
        if entities.job_titles:
            primary_role = entities.job_titles[0].title()
            sentence1 = f"The candidate is a {primary_role}."
            if len(entities.job_titles) > 1:
                sentence1 = (
                    f"The candidate is a {primary_role} with experience in "
                    f"{', '.join(t.title() for t in entities.job_titles[1:3])}."
                )
            sentences.append(sentence1)

        # Sentence 2: Technical skills (programming languages and frameworks)
        technical_skills_parts = []
        if entities.programming_languages:
            langs = entities.programming_languages[:5]
            technical_skills_parts.append(
                f"proficient in {', '.join(lang.title() for lang in langs)}"
            )
        if entities.frameworks:
            frameworks = entities.frameworks[:3]
            technical_skills_parts.append(
                f"experienced with {', '.join(fw.title() for fw in frameworks)}"
            )
        if entities.databases:
            dbs = entities.databases[:3]
            technical_skills_parts.append(
                f"familiar with {', '.join(db.title() for db in dbs)}"
            )

        if technical_skills_parts:
            sentence2 = f"The candidate is {', '.join(technical_skills_parts[:2])}."
            sentences.append(sentence2)

        # Sentence 3: Additional technical skills (tools, cloud platforms)
        additional_skills = []
        if entities.tools:
            tools = entities.tools[:3]
            additional_skills.append(
                f"tools such as {', '.join(tool.title() for tool in tools)}"
            )
        if entities.cloud_platforms:
            clouds = entities.cloud_platforms[:2]
            additional_skills.append(
                f"cloud platforms including {', '.join(c.title() for c in clouds)}"
            )

        if additional_skills:
            sentence3 = (
                f"The candidate has experience with " f"{', '.join(additional_skills)}."
            )
            sentences.append(sentence3)

        # Sentence 4: Qualifications (education and certifications)
        qualifications = []
        if entities.degrees:
            degrees_text = ", ".join(d.title() for d in entities.degrees[:2])
            qualifications.append(f"holds {degrees_text}")
        if entities.certifications:
            certs_text = ", ".join(
                c.title() if c else "relevant certifications"
                for c in entities.certifications[:2]
            )
            qualifications.append(f"has {certs_text}")

        if qualifications:
            sentence4 = f"The candidate {', '.join(qualifications)}."
            sentences.append(sentence4)

        # Sentence 5: Soft skills and languages (if available)
        additional_info = []
        if entities.soft_skills:
            soft = entities.soft_skills[:3]
            additional_info.append(f"demonstrates {', '.join(s.title() for s in soft)}")
        if entities.languages:
            langs = entities.languages[:3]
            additional_info.append(
                f"communicates in {', '.join(lang.title() for lang in langs)}"
            )

        if additional_info and len(sentences) < 5:
            sentence5 = f"The candidate {', '.join(additional_info[:1])}."
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

        # Sentence 1: Professional role/positions
        if entities.job_titles:
            primary_role = entities.job_titles[0].title()
            sentence1 = f"A jelölt {primary_role} pozícióban dolgozik."
            if len(entities.job_titles) > 1:
                sentence1 = (
                    f"A jelölt {primary_role} pozícióban dolgozik, "
                    f"tapasztalattal rendelkezik a következő területeken: "
                    f"{', '.join(t.title() for t in entities.job_titles[1:3])}."
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
        qualifications = []
        if entities.degrees:
            degrees_text = ", ".join(d.title() for d in entities.degrees[:2])
            qualifications.append(f"{degrees_text} végzettséggel rendelkezik")
        if entities.certifications:
            certs_text = ", ".join(
                c.title() if c else "releváns tanúsítványok"
                for c in entities.certifications[:2]
            )
            qualifications.append(f"rendelkezik {certs_text}")

        if qualifications:
            sentence4 = f"A jelölt {', '.join(qualifications)}."
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
