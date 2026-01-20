"""
Bias pattern detection for ranking results.
Analyzes score distributions and identifies potential fairness issues.
"""

import logging
from typing import Any, Dict, List, Optional
from decimal import Decimal
import statistics

logger = logging.getLogger(__name__)


class BiasPatternDetector:
    """
    Analyzes ranking results for potential bias patterns.
    Provides statistical analysis and bias indicators.
    """
    
    def __init__(
        self,
        *,
        score_variance_threshold: float = 0.15,
        clustering_threshold: float = 0.80,
        min_sample_size: int = 10
    ):
        """
        Initialize bias detector with thresholds.
        
        Args:
            score_variance_threshold: Max acceptable variance in scores
            clustering_threshold: Threshold for detecting score clustering
            min_sample_size: Minimum samples needed for analysis
        """
        self.score_variance_threshold = score_variance_threshold
        self.clustering_threshold = clustering_threshold
        self.min_sample_size = min_sample_size
    
    def analyze_score_distribution(
        self,
        scores: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze score distribution for bias indicators.
        
        Args:
            scores: List of candidate scores (0-100 or 0-1 range)
            metadata: Optional ranking run metadata
        
        Returns:
            {
                'has_bias_indicators': bool,
                'score_statistics': {...},
                'alerts': [...],
                'recommendations': [...]
            }
        """
        if not scores or len(scores) < self.min_sample_size:
            return {
                'has_bias_indicators': False,
                'score_statistics': {},
                'alerts': [],
                'recommendations': ['Insufficient data for bias analysis'],
                'sample_size_too_small': True
            }
        
        # Convert Decimal to float if needed
        scores = [float(s) for s in scores]
        
        # Calculate statistics
        stats = self._calculate_statistics(scores)
        
        # Detect bias patterns
        alerts = []
        
        # 1. Check for low variance (all scores too similar)
        if stats['variance'] < self.score_variance_threshold:
            alerts.append({
                'type': 'low_variance',
                'severity': 'warning',
                'message': f'Score variance ({stats["variance"]:.3f}) is very low. '
                          f'May indicate insufficient differentiation.',
                'metric': stats['variance'],
                'threshold': self.score_variance_threshold
            })
        
        # 2. Check for score clustering (many scores in same range)
        clustering_ratio = self._detect_clustering(scores)
        if clustering_ratio > self.clustering_threshold:
            alerts.append({
                'type': 'score_clustering',
                'severity': 'warning',
                'message': f'{clustering_ratio*100:.1f}% of scores clustered in similar range. '
                          f'May indicate bias towards certain criteria.',
                'metric': clustering_ratio,
                'threshold': self.clustering_threshold
            })
        
        # 3. Check for extreme skewness
        if stats['skewness'] and abs(stats['skewness']) > 1.5:
            alerts.append({
                'type': 'skewed_distribution',
                'severity': 'info',
                'message': f'Scores are highly skewed ({stats["skewness"]:.2f}). '
                          f'Consider reviewing criteria weights.',
                'metric': stats['skewness']
            })
        
        # 4. Check for unusual gaps in score distribution
        gaps = self._detect_score_gaps(scores)
        if gaps:
            alerts.append({
                'type': 'score_gaps',
                'severity': 'info',
                'message': f'Found {len(gaps)} unusual gaps in score distribution. '
                          f'May indicate missing middle-ground candidates.',
                'gaps': gaps
            })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(alerts, stats)
        
        return {
            'has_bias_indicators': len(alerts) > 0,
            'score_statistics': stats,
            'alerts': alerts,
            'recommendations': recommendations,
            'sample_size': len(scores)
        }
    
    def _calculate_statistics(self, scores: List[float]) -> Dict[str, Any]:
        """Calculate statistical measures for scores."""
        if not scores:
            return {}
        
        sorted_scores = sorted(scores)
        
        stats = {
            'count': len(scores),
            'min': min(scores),
            'max': max(scores),
            'mean': statistics.mean(scores),
            'median': statistics.median(scores),
            'variance': statistics.variance(scores) if len(scores) > 1 else 0.0,
            'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0.0,
        }
        
        # Add quartiles
        if len(scores) >= 4:
            stats['q1'] = statistics.quantiles(scores, n=4)[0]
            stats['q3'] = statistics.quantiles(scores, n=4)[2]
            stats['iqr'] = stats['q3'] - stats['q1']
        
        # Calculate skewness (basic approximation)
        if stats.get('std_dev', 0) > 0:
            mean_diff = [x - stats['mean'] for x in scores]
            skewness = sum([x**3 for x in mean_diff]) / (len(scores) * (stats['std_dev'] ** 3))
            stats['skewness'] = skewness
        else:
            stats['skewness'] = None
        
        return stats
    
    def _detect_clustering(self, scores: List[float]) -> float:
        """
        Detect if scores are clustered in a narrow range.
        Returns ratio of scores within the most common range.
        """
        if not scores or len(scores) < 5:
            return 0.0
        
        sorted_scores = sorted(scores)
        
        # Divide into 10 bins
        min_score = min(scores)
        max_score = max(scores)
        range_width = (max_score - min_score) / 10 if max_score > min_score else 1.0
        
        if range_width == 0:
            return 1.0  # All scores identical
        
        # Count scores in each bin
        bins = {}
        for score in scores:
            bin_idx = int((score - min_score) / range_width)
            if bin_idx == 10:  # Edge case for max score
                bin_idx = 9
            bins[bin_idx] = bins.get(bin_idx, 0) + 1
        
        # Find maximum bin count
        max_bin_count = max(bins.values()) if bins else 0
        
        # Return ratio of scores in most populated bin
        return max_bin_count / len(scores)
    
    def _detect_score_gaps(self, scores: List[float]) -> List[Dict[str, float]]:
        """
        Detect unusual gaps in score distribution.
        Returns list of gaps with their positions.
        """
        if not scores or len(scores) < 3:
            return []
        
        sorted_scores = sorted(scores)
        
        # Calculate average gap
        gaps = [sorted_scores[i+1] - sorted_scores[i] for i in range(len(sorted_scores)-1)]
        avg_gap = statistics.mean(gaps) if gaps else 0
        
        # Find gaps larger than 3x average
        unusual_gaps = []
        for i, gap in enumerate(gaps):
            if gap > 3 * avg_gap and gap > 0.1:  # Significant gap
                unusual_gaps.append({
                    'position': i,
                    'gap_size': round(gap, 3),
                    'before_score': round(sorted_scores[i], 3),
                    'after_score': round(sorted_scores[i+1], 3)
                })
        
        return unusual_gaps
    
    def _generate_recommendations(
        self, 
        alerts: List[Dict], 
        stats: Dict
    ) -> List[str]:
        """Generate actionable recommendations based on alerts."""
        recommendations = []
        
        alert_types = {alert['type'] for alert in alerts}
        
        if 'low_variance' in alert_types:
            recommendations.append(
                'Consider reviewing criteria weights to create more differentiation between candidates.'
            )
            recommendations.append(
                'Verify that scoring components are using their full range (0-100).'
            )
        
        if 'score_clustering' in alert_types:
            recommendations.append(
                'Investigate if criteria are too lenient or strict, causing score clustering.'
            )
            recommendations.append(
                'Consider adding more discriminating criteria to better differentiate candidates.'
            )
        
        if 'skewed_distribution' in alert_types:
            skew = stats.get('skewness', 0)
            if skew and skew > 0:
                recommendations.append(
                    'Scores are skewed towards lower values. Consider if criteria are too strict.'
                )
            elif skew and skew < 0:
                recommendations.append(
                    'Scores are skewed towards higher values. Consider if criteria are too lenient.'
                )
        
        if 'score_gaps' in alert_types:
            recommendations.append(
                'Large gaps in score distribution detected. Review criteria for potential bias.'
            )
        
        if not recommendations:
            recommendations.append(
                'Score distribution appears healthy. No immediate concerns detected.'
            )
        
        return recommendations
    
    def generate_bias_report(
        self,
        scores: List[float],
        run_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive bias analysis report.
        
        Args:
            scores: List of candidate scores
            run_metadata: Optional ranking run metadata
        
        Returns:
            Complete bias analysis report
        """
        analysis = self.analyze_score_distribution(scores, run_metadata)
        
        # Add severity summary
        severity_counts = {
            'error': 0,
            'warning': 0,
            'info': 0
        }
        
        for alert in analysis['alerts']:
            severity = alert.get('severity', 'info')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        report = {
            'analysis': analysis,
            'severity_summary': severity_counts,
            'overall_assessment': self._get_overall_assessment(analysis),
            'requires_review': severity_counts.get('error', 0) > 0 or severity_counts.get('warning', 0) > 0,
            'metadata': run_metadata or {}
        }
        
        return report
    
    def _get_overall_assessment(self, analysis: Dict) -> str:
        """Get overall assessment of bias analysis."""
        if not analysis['has_bias_indicators']:
            return 'HEALTHY'
        
        alert_severities = [alert.get('severity', 'info') for alert in analysis['alerts']]
        
        if 'error' in alert_severities:
            return 'CRITICAL'
        elif 'warning' in alert_severities:
            return 'NEEDS_ATTENTION'
        else:
            return 'INFORMATIONAL'
