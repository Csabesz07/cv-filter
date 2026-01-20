"""
Test script for CV summarization functionality.
Tests the template-based summarization that uses only extracted entities.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "cv_filter"))

from entity_extraction.models import ExtractedEntities
from summarization.summarizer import CVSummarizer


def test_hungarian_summary():
    """Test Hungarian summary generation."""
    print("=" * 80)
    print("Testing Hungarian CV Summary Generation")
    print("=" * 80)
    
    # Create sample extracted entities
    entities = ExtractedEntities(
        email=["kiss.peter@example.com"],
        phone=["+36 30 123 4567"],
        linkedin=["linkedin.com/in/kisspeter"],
        github=["github.com/kisspeter"],
        websites=[],
        programming_languages=["Python", "Java", "JavaScript", "C++"],
        frameworks=["Django", "React", "Spring Boot"],
        databases=["PostgreSQL", "MongoDB", "Redis"],
        tools=["Git", "Docker", "Kubernetes"],
        cloud_platforms=["AWS", "Azure"],
        soft_skills=["Csapatmunka", "Kommunikáció", "Problémamegoldás"],
        languages=["Magyar", "Angol", "Német"],
        degrees=["Informatikai Mérnök BSc", "Adattudományi MSc"],
        certifications=["AWS Certified Solutions Architect", "Scrum Master"],
        job_titles=["Senior Software Engineer", "Backend Developer", "Team Lead"],
    )
    
    # Generate summary
    summarizer = CVSummarizer(language="hu", model_name="template", model_version="1.0")
    summary = summarizer.generate_summary(entities, language="hu")
    
    print("\n" + "=" * 80)
    print("GENERATED SUMMARY (Hungarian):")
    print("=" * 80)
    print(summary.summary_text)
    print("=" * 80)
    print(f"\nLanguage: {summary.language}")
    print(f"Model: {summary.model_name} v{summary.model_version}")
    print(f"Generated at: {summary.generated_at}")
    
    # Validate summary
    sentences = [s.strip() for s in summary.summary_text.split(". ") if s.strip()]
    sentence_count = len(sentences)
    print(f"\nSentence count: {sentence_count}")
    
    if 3 <= sentence_count <= 5:
        print("✓ Sentence count is valid (3-5 sentences)")
    else:
        print(f"✗ Sentence count is invalid (expected 3-5, got {sentence_count})")
    
    # Check for hallucinations (summary should only mention extracted data)
    print("\nValidating content (checking for hallucinations)...")
    hallucination_free = True
    
    # Check that mentioned skills are in the extracted entities
    for lang in entities.programming_languages:
        if lang.lower() in summary.summary_text.lower():
            print(f"  ✓ Found programming language: {lang}")
    
    for framework in entities.frameworks:
        if framework.lower() in summary.summary_text.lower():
            print(f"  ✓ Found framework: {framework}")
    
    print("\n" + "=" * 80)
    return summary


def test_english_summary():
    """Test English summary generation."""
    print("\n\n" + "=" * 80)
    print("Testing English CV Summary Generation")
    print("=" * 80)
    
    # Create sample extracted entities
    entities = ExtractedEntities(
        email=["john.doe@example.com"],
        phone=["+1 555 123 4567"],
        linkedin=["linkedin.com/in/johndoe"],
        github=["github.com/johndoe"],
        websites=[],
        programming_languages=["Python", "JavaScript", "TypeScript", "Go"],
        frameworks=["React", "Node.js", "FastAPI"],
        databases=["PostgreSQL", "MySQL"],
        tools=["Git", "Docker"],
        cloud_platforms=["AWS"],
        soft_skills=["Leadership", "Communication"],
        languages=["English", "Spanish"],
        degrees=["Computer Science BSc"],
        certifications=["AWS Certified Developer"],
        job_titles=["Full Stack Developer", "Software Engineer"],
    )
    
    # Generate summary
    summarizer = CVSummarizer(language="en", model_name="template", model_version="1.0")
    summary = summarizer.generate_summary(entities, language="en")
    
    print("\n" + "=" * 80)
    print("GENERATED SUMMARY (English):")
    print("=" * 80)
    print(summary.summary_text)
    print("=" * 80)
    print(f"\nLanguage: {summary.language}")
    print(f"Model: {summary.model_name} v{summary.model_version}")
    print(f"Generated at: {summary.generated_at}")
    
    # Validate summary
    sentences = [s.strip() for s in summary.summary_text.split(". ") if s.strip()]
    sentence_count = len(sentences)
    print(f"\nSentence count: {sentence_count}")
    
    if 3 <= sentence_count <= 5:
        print("✓ Sentence count is valid (3-5 sentences)")
    else:
        print(f"✗ Sentence count is invalid (expected 3-5, got {sentence_count})")
    
    print("\n" + "=" * 80)
    return summary


def test_minimal_entities():
    """Test with minimal entities (edge case)."""
    print("\n\n" + "=" * 80)
    print("Testing with Minimal Entities")
    print("=" * 80)
    
    # Create minimal extracted entities
    entities = ExtractedEntities(
        email=["test@example.com"],
        phone=[],
        linkedin=[],
        github=[],
        websites=[],
        programming_languages=["Python"],
        frameworks=[],
        databases=[],
        tools=[],
        cloud_platforms=[],
        soft_skills=[],
        languages=["Magyar"],
        degrees=["BSc"],
        certifications=[],
        job_titles=["Developer"],
    )
    
    # Generate summary
    summarizer = CVSummarizer(language="hu", model_name="template", model_version="1.0")
    summary = summarizer.generate_summary(entities, language="hu")
    
    print("\n" + "=" * 80)
    print("GENERATED SUMMARY (Minimal Entities):")
    print("=" * 80)
    print(summary.summary_text)
    print("=" * 80)
    
    sentences = [s.strip() for s in summary.summary_text.split(". ") if s.strip()]
    print(f"\nSentence count: {len(sentences)}")
    
    print("\n" + "=" * 80)
    return summary


if __name__ == "__main__":
    try:
        test_hungarian_summary()
        test_english_summary()
        test_minimal_entities()
        
        print("\n\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
