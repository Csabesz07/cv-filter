#!/usr/bin/env python
"""
Script to regenerate all CV summaries with the improved template.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_filter.settings')
django.setup()

from entity_extraction.models import ExtractedEntities
from accounts.models import CandidateStructuredData, CVParse, CandidateSummary
from summarization.summarizer import CVSummarizer
from django.utils import timezone


def regenerate_all_summaries():
    """Regenerate all CV summaries with the new template."""
    
    # Get all structured data (contains extracted entities)
    all_structured_data = CandidateStructuredData.objects.select_related('cv_parse').all()
    total = all_structured_data.count()
    
    if total == 0:
        print("No structured data found.")
        return
    
    print(f"Found {total} structured data entries. Regenerating summaries...")
    
    # Initialize summarizer
    summarizer_en = CVSummarizer(language="en")
    
    updated = 0
    created = 0
    skipped = 0
    errors = 0
    
    for i, structured_data in enumerate(all_structured_data, 1):
        try:
            # Skip if no structured JSON
            if not structured_data.structured_json:
                print(f"\n[{i}/{total}] Skipping - no structured JSON")
                skipped += 1
                continue
            
            # Convert to ExtractedEntities
            entities = ExtractedEntities.from_dict(structured_data.structured_json)
            
            # Get CV parse and candidate
            cv_parse = structured_data.cv_parse
            cv_file = cv_parse.cv_file
            candidate = cv_file.candidate
            organization = structured_data.organization
            
            print(f"\n[{i}/{total}] Processing candidate: {candidate.first_name} {candidate.last_name}...")
            
            # Generate new summary (English)
            summary_obj = summarizer_en.generate_summary(entities, language="en")
            
            # Check if summary already exists
            existing_summary = CandidateSummary.objects.filter(
                candidate=candidate,
                cv_parse=cv_parse
            ).first()
            
            if existing_summary:
                # Update existing
                old_text = existing_summary.summary_text
                existing_summary.summary_text = summary_obj.summary_text
                existing_summary.language = summary_obj.language
                existing_summary.model_name = summary_obj.model_name
                existing_summary.model_version = summary_obj.model_version
                existing_summary.generated_at = timezone.now()
                existing_summary.summary_status = 'succeeded'
                existing_summary.save()
                
                print(f"  ✓ Updated summary")
                if old_text:
                    print(f"  Old: {old_text[:80]}...")
                print(f"  New: {summary_obj.summary_text[:80]}...")
                updated += 1
            else:
                # Create new
                CandidateSummary.objects.create(
                    organization=organization,
                    candidate=candidate,
                    cv_parse=cv_parse,
                    summary_text=summary_obj.summary_text,
                    language=summary_obj.language,
                    model_name=summary_obj.model_name,
                    model_version=summary_obj.model_version,
                    prompt_version=summary_obj.prompt_version,
                    generated_at=timezone.now(),
                    summary_status='succeeded'
                )
                print(f"  ✓ Created summary: {summary_obj.summary_text[:80]}...")
                created += 1
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"Summary regeneration complete!")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total processed: {created + updated}")
    print(f"{'='*60}")


if __name__ == "__main__":
    regenerate_all_summaries()
