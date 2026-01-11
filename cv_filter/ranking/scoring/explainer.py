"""
Explanation generator for scoring results.
Generates human-readable explanations in Hungarian and English.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ScoringExplainer:
    """
    Generates human-readable explanations for scoring results.
    Supports both Hungarian and English languages.
    """

    def __init__(self, default_language: str = "hu"):
        """
        Initialize explainer.

        Args:
            default_language: Default language ('hu' or 'en')
        """
        self.default_language = default_language

    def generate_explanation(
        self,
        total_score: float,
        component_scores: Dict[str, float],
        skill_details: Dict[str, Any],
        experience_details: Dict[str, Any],
        education_details: Dict[str, Any],
        candidate_data: Dict[str, Any],
        criteria: Dict[str, Any],
        language: str = None,
    ) -> str:
        """
        Generate comprehensive explanation for a score.

        Args:
            total_score: Total score (0-100)
            component_scores: Component scores (0-1.0)
            skill_details: Skill matching details
            experience_details: Experience scoring details
            education_details: Education scoring details
            candidate_data: Candidate information
            criteria: Job requirements
            language: Language for explanation ('hu' or 'en')

        Returns:
            Human-readable explanation text
        """
        lang = language or self.default_language
        
        if lang == "hu":
            return self._generate_explanation_hu(
                total_score,
                component_scores,
                skill_details,
                experience_details,
                education_details,
            )
        else:
            return self._generate_explanation_en(
                total_score,
                component_scores,
                skill_details,
                experience_details,
                education_details,
            )

    def _generate_explanation_hu(
        self,
        total_score: float,
        component_scores: Dict[str, float],
        skill_details: Dict[str, Any],
        experience_details: Dict[str, Any],
        education_details: Dict[str, Any],
    ) -> str:
        """Generate Hungarian explanation."""
        
        # Opening assessment
        assessment = self._get_assessment_hu(total_score)
        lines = [f"{assessment} ({total_score:.1f}/100 pont)"]
        
        # Skills section
        skill_score = component_scores['skills'] * 100
        skill_matched = skill_details['details'].get('required_matched', 0)
        skill_total = skill_details['details'].get('required_total', 0)
        
        if skill_total > 0:
            match_quality = skill_details['details'].get('match_quality', 'good')
            quality_hu = {
                'excellent': 'kiváló',
                'strong': 'erős',
                'good': 'jó',
                'fair': 'elfogadható',
                'weak': 'gyenge'
            }.get(match_quality, 'közepes')
            
            lines.append(
                f"\nKészségek ({skill_score:.0f}%): {skill_matched}/{skill_total} "
                f"követelménynek megfelel - {quality_hu} egyezés"
            )
            
            # Matched skills
            if skill_details.get('matched'):
                matched_sample = ', '.join(skill_details['matched'][:5])
                if len(skill_details['matched']) > 5:
                    matched_sample += f" (+{len(skill_details['matched']) - 5} további)"
                lines.append(f"  ✓ Megvan: {matched_sample}")
            
            # Missing skills
            if skill_details.get('missing'):
                missing_sample = ', '.join(skill_details['missing'][:3])
                if len(skill_details['missing']) > 3:
                    missing_sample += f" (+{len(skill_details['missing']) - 3} további)"
                lines.append(f"  ✗ Hiányzik: {missing_sample}")
        
        # Experience section
        exp_score = component_scores['experience'] * 100
        exp_years = experience_details['details'].get('candidate_years', 0)
        min_years = experience_details['details'].get('required_minimum', 0)
        meets_min = experience_details['details'].get('meets_minimum', False)
        
        if min_years > 0:
            status = "teljesíti" if meets_min else "nem teljesíti"
            lines.append(
                f"\nTapasztalat ({exp_score:.0f}%): {exp_years:.1f} év "
                f"({status} a minimum {min_years} évet)"
            )
            
            if experience_details.get('matched'):
                lines.append(f"  ✓ {', '.join(experience_details['matched'][:2])}")
            if experience_details.get('missing'):
                lines.append(f"  ✗ {', '.join(experience_details['missing'][:2])}")
        
        # Education section
        edu_score = component_scores['education'] * 100
        edu_level = education_details['details'].get('candidate_level', 'none')
        req_level = education_details['details'].get('required_level', 'bachelor')
        
        if edu_level != 'none':
            edu_level_hu = {
                'high_school': 'Középiskola',
                'associate': 'Asszisztens',
                'bachelor': 'Alapdiploma',
                'master': 'Mester',
                'phd': 'PhD'
            }.get(edu_level, edu_level.replace('_', ' ').title())
            
            lines.append(
                f"\nVégzettség ({edu_score:.0f}%): {edu_level_hu}"
            )
            
            if education_details.get('matched'):
                lines.append(f"  ✓ {', '.join(education_details['matched'][:2])}")
        
        # Recommendation
        if total_score >= 75:
            lines.append(
                "\n💡 Ajánlás: Erősen ajánlott jelölt, érdemes meghívni interjúra."
            )
        elif total_score >= 60:
            lines.append(
                "\n💡 Ajánlás: Megfelelő jelölt, megfontolásra ajánlott."
            )
        elif total_score >= 40:
            lines.append(
                "\n💡 Ajánlás: Lehetséges jelölt hiányzó készségekkel, megfontolás szükséges."
            )
        else:
            lines.append(
                "\n💡 Ajánlás: Nem felel meg a követelményeknek."
            )
        
        return '\n'.join(lines)

    def _generate_explanation_en(
        self,
        total_score: float,
        component_scores: Dict[str, float],
        skill_details: Dict[str, Any],
        experience_details: Dict[str, Any],
        education_details: Dict[str, Any],
    ) -> str:
        """Generate English explanation."""
        
        # Opening assessment
        assessment = self._get_assessment_en(total_score)
        lines = [f"{assessment} ({total_score:.1f}/100 points)"]
        
        # Skills section
        skill_score = component_scores['skills'] * 100
        skill_matched = skill_details['details'].get('required_matched', 0)
        skill_total = skill_details['details'].get('required_total', 0)
        
        if skill_total > 0:
            match_quality = skill_details['details'].get('match_quality', 'good')
            
            lines.append(
                f"\nSkills ({skill_score:.0f}%): {skill_matched}/{skill_total} "
                f"required skills matched - {match_quality} match"
            )
            
            # Matched skills
            if skill_details.get('matched'):
                matched_sample = ', '.join(skill_details['matched'][:5])
                if len(skill_details['matched']) > 5:
                    matched_sample += f" (+{len(skill_details['matched']) - 5} more)"
                lines.append(f"  ✓ Has: {matched_sample}")
            
            # Missing skills
            if skill_details.get('missing'):
                missing_sample = ', '.join(skill_details['missing'][:3])
                if len(skill_details['missing']) > 3:
                    missing_sample += f" (+{len(skill_details['missing']) - 3} more)"
                lines.append(f"  ✗ Missing: {missing_sample}")
        
        # Experience section
        exp_score = component_scores['experience'] * 100
        exp_years = experience_details['details'].get('candidate_years', 0)
        min_years = experience_details['details'].get('required_minimum', 0)
        meets_min = experience_details['details'].get('meets_minimum', False)
        
        if min_years > 0:
            status = "meets" if meets_min else "does not meet"
            lines.append(
                f"\nExperience ({exp_score:.0f}%): {exp_years:.1f} years "
                f"({status} {min_years}+ year requirement)"
            )
            
            if experience_details.get('matched'):
                lines.append(f"  ✓ {', '.join(experience_details['matched'][:2])}")
            if experience_details.get('missing'):
                lines.append(f"  ✗ {', '.join(experience_details['missing'][:2])}")
        
        # Education section
        edu_score = component_scores['education'] * 100
        edu_level = education_details['details'].get('candidate_level', 'none')
        
        if edu_level != 'none':
            edu_level_display = edu_level.replace('_', ' ').title()
            
            lines.append(
                f"\nEducation ({edu_score:.0f}%): {edu_level_display}"
            )
            
            if education_details.get('matched'):
                lines.append(f"  ✓ {', '.join(education_details['matched'][:2])}")
        
        # Recommendation
        if total_score >= 75:
            lines.append(
                "\n💡 Recommendation: Highly recommended candidate, should invite for interview."
            )
        elif total_score >= 60:
            lines.append(
                "\n💡 Recommendation: Good candidate, worth considering."
            )
        elif total_score >= 40:
            lines.append(
                "\n💡 Recommendation: Potential candidate with gaps, requires consideration."
            )
        else:
            lines.append(
                "\n💡 Recommendation: Does not meet requirements."
            )
        
        return '\n'.join(lines)

    def _get_assessment_hu(self, score: float) -> str:
        """Get Hungarian quality assessment."""
        if score >= 90:
            return "Kiváló egyezés"
        elif score >= 80:
            return "Nagyon jó egyezés"
        elif score >= 70:
            return "Jó egyezés"
        elif score >= 60:
            return "Közepes egyezés"
        elif score >= 50:
            return "Elfogadható egyezés"
        elif score >= 40:
            return "Gyenge egyezés"
        else:
            return "Nem megfelelő"

    def _get_assessment_en(self, score: float) -> str:
        """Get English quality assessment."""
        if score >= 90:
            return "Excellent match"
        elif score >= 80:
            return "Very good match"
        elif score >= 70:
            return "Good match"
        elif score >= 60:
            return "Moderate match"
        elif score >= 50:
            return "Fair match"
        elif score >= 40:
            return "Weak match"
        else:
            return "Poor match"

    def generate_short_summary(
        self,
        total_score: float,
        component_scores: Dict[str, float],
        language: str = None,
    ) -> str:
        """
        Generate short one-line summary.

        Args:
            total_score: Total score (0-100)
            component_scores: Component scores
            language: Language ('hu' or 'en')

        Returns:
            Short summary string
        """
        lang = language or self.default_language
        
        skill_pct = int(component_scores['skills'] * 100)
        exp_pct = int(component_scores['experience'] * 100)
        edu_pct = int(component_scores['education'] * 100)
        
        if lang == "hu":
            return (
                f"{total_score:.0f}/100 pont "
                f"(Készségek: {skill_pct}%, Tapasztalat: {exp_pct}%, Végzettség: {edu_pct}%)"
            )
        else:
            return (
                f"{total_score:.0f}/100 points "
                f"(Skills: {skill_pct}%, Experience: {exp_pct}%, Education: {edu_pct}%)"
            )
