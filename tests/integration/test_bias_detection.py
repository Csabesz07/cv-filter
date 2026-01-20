"""
Test script for bias pattern detection.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "cv_filter"))

from ranking.bias_detector import BiasPatternDetector


def test_healthy_distribution():
    """Test with healthy, well-distributed scores."""
    print("=" * 80)
    print("Test 1: Healthy Score Distribution")
    print("=" * 80)
    
    # Well distributed scores
    scores = [
        45, 52, 58, 61, 65, 68, 72, 74, 76, 78,
        80, 81, 83, 85, 86, 88, 89, 91, 92, 94
    ]
    
    detector = BiasPatternDetector()
    analysis = detector.analyze_score_distribution(scores)
    
    print(f"\nSample Size: {analysis['sample_size']}")
    print(f"Has Bias Indicators: {analysis['has_bias_indicators']}")
    
    print("\nScore Statistics:")
    stats = analysis['score_statistics']
    print(f"  Mean: {stats['mean']:.2f}")
    print(f"  Median: {stats['median']:.2f}")
    print(f"  Std Dev: {stats['std_dev']:.2f}")
    print(f"  Variance: {stats['variance']:.2f}")
    print(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")
    
    if analysis['alerts']:
        print(f"\nAlerts ({len(analysis['alerts'])}):")
        for alert in analysis['alerts']:
            print(f"  [{alert['severity'].upper()}] {alert['type']}: {alert['message']}")
    else:
        print("\nNo alerts - healthy distribution!")
    
    print("\nRecommendations:")
    for rec in analysis['recommendations']:
        print(f"  • {rec}")
    
    print("\n" + "=" * 80)


def test_clustered_scores():
    """Test with clustered scores (potential bias)."""
    print("\n" + "=" * 80)
    print("Test 2: Clustered Score Distribution (Bias Indicator)")
    print("=" * 80)
    
    # Most scores clustered around 75-80
    scores = [
        76, 77, 77, 78, 78, 78, 79, 79, 79, 79,
        80, 80, 80, 81, 81, 82, 45, 50, 90, 92
    ]
    
    detector = BiasPatternDetector()
    analysis = detector.analyze_score_distribution(scores)
    
    print(f"\nSample Size: {analysis['sample_size']}")
    print(f"Has Bias Indicators: {analysis['has_bias_indicators']}")
    
    print("\nScore Statistics:")
    stats = analysis['score_statistics']
    print(f"  Mean: {stats['mean']:.2f}")
    print(f"  Median: {stats['median']:.2f}")
    print(f"  Variance: {stats['variance']:.2f}")
    
    print(f"\nAlerts ({len(analysis['alerts'])}):")
    for alert in analysis['alerts']:
        print(f"  [{alert['severity'].upper()}] {alert['type']}:")
        print(f"    {alert['message']}")
    
    print("\nRecommendations:")
    for rec in analysis['recommendations']:
        print(f"  • {rec}")
    
    print("\n" + "=" * 80)


def test_low_variance():
    """Test with very similar scores (low variance)."""
    print("\n" + "=" * 80)
    print("Test 3: Low Variance Distribution (Bias Indicator)")
    print("=" * 80)
    
    # All scores very similar
    scores = [
        68, 69, 69, 70, 70, 70, 71, 71, 71, 72,
        72, 72, 73, 73, 73, 74, 74, 75, 75, 76
    ]
    
    detector = BiasPatternDetector()
    analysis = detector.analyze_score_distribution(scores)
    
    print(f"\nSample Size: {analysis['sample_size']}")
    print(f"Has Bias Indicators: {analysis['has_bias_indicators']}")
    
    print("\nScore Statistics:")
    stats = analysis['score_statistics']
    print(f"  Mean: {stats['mean']:.2f}")
    print(f"  Variance: {stats['variance']:.2f}")
    print(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")
    print(f"  Std Dev: {stats['std_dev']:.2f}")
    
    print(f"\nAlerts ({len(analysis['alerts'])}):")
    for alert in analysis['alerts']:
        print(f"  [{alert['severity'].upper()}] {alert['type']}:")
        print(f"    {alert['message']}")
    
    print("\nRecommendations:")
    for rec in analysis['recommendations']:
        print(f"  • {rec}")
    
    print("\n" + "=" * 80)


def test_bias_report():
    """Test full bias report generation."""
    print("\n" + "=" * 80)
    print("Test 4: Full Bias Report")
    print("=" * 80)
    
    scores = [
        30, 35, 40, 75, 76, 77, 78, 78, 79, 80,
        80, 81, 81, 82, 85, 90, 92, 94, 95, 98
    ]
    
    metadata = {
        'run_id': 'test-run-123',
        'criteria': ['skills', 'experience', 'education'],
        'has_bias_config': False
    }
    
    detector = BiasPatternDetector()
    report = detector.generate_bias_report(scores, metadata)
    
    print(f"\nOverall Assessment: {report['overall_assessment']}")
    print(f"Requires Review: {report['requires_review']}")
    
    print("\nSeverity Summary:")
    for severity, count in report['severity_summary'].items():
        if count > 0:
            print(f"  {severity.upper()}: {count}")
    
    print("\nScore Distribution:")
    stats = report['analysis']['score_statistics']
    print(f"  Mean: {stats['mean']:.2f}")
    print(f"  Median: {stats['median']:.2f}")
    print(f"  Std Dev: {stats['std_dev']:.2f}")
    print(f"  Range: {stats['min']:.2f} - {stats['max']:.2f}")
    
    if report['analysis']['alerts']:
        print(f"\nBias Indicators ({len(report['analysis']['alerts'])}):")
        for alert in report['analysis']['alerts']:
            print(f"  [{alert['severity'].upper()}] {alert['type']}")
    
    print("\nRecommendations:")
    for rec in report['analysis']['recommendations']:
        print(f"  • {rec}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        test_healthy_distribution()
        test_clustered_scores()
        test_low_variance()
        test_bias_report()
        
        print("\n\n" + "=" * 80)
        print("ALL BIAS DETECTION TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
