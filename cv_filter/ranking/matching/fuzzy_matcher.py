"""
Fuzzy string matching for skill and keyword comparison.
"""

import logging
from typing import List, Tuple

try:
    from fuzzywuzzy import fuzz
except ImportError:
    # Fallback to difflib if fuzzywuzzy not available
    import difflib

    class fuzz:
        @staticmethod
        def ratio(s1: str, s2: str) -> int:
            return int(difflib.SequenceMatcher(None, s1, s2).ratio() * 100)

logger = logging.getLogger(__name__)


class FuzzyMatcher:
    """
    Fuzzy string matching for handling typos, variations, and similar terms.
    """

    def __init__(self, threshold: int = 85):
        """
        Initialize fuzzy matcher.

        Args:
            threshold: Minimum similarity score (0-100) to consider a match
        """
        self.threshold = threshold

    def match(self, term1: str, term2: str) -> bool:
        """
        Check if two terms match within threshold.

        Args:
            term1: First term to compare
            term2: Second term to compare

        Returns:
            True if similarity >= threshold

        Examples:
            >>> matcher = FuzzyMatcher(threshold=85)
            >>> matcher.match("PostgreSQL", "Postgres")
            True
            >>> matcher.match("React", "Angular")
            False
        """
        score = self.similarity(term1, term2)
        return score >= self.threshold

    def similarity(self, term1: str, term2: str) -> int:
        """
        Calculate similarity score between two terms.

        Args:
            term1: First term
            term2: Second term

        Returns:
            Similarity score (0-100)
        """
        if not term1 or not term2:
            return 0

        # Normalize: lowercase, strip whitespace
        t1 = term1.lower().strip()
        t2 = term2.lower().strip()

        # Exact match
        if t1 == t2:
            return 100

        # Fuzzy match
        return fuzz.ratio(t1, t2)

    def find_best_match(
        self, query: str, candidates: List[str]
    ) -> Tuple[str, int]:
        """
        Find best matching candidate for a query term.

        Args:
            query: Term to search for
            candidates: List of candidate terms

        Returns:
            Tuple of (best_match, score). Returns (None, 0) if no match above threshold.

        Examples:
            >>> matcher = FuzzyMatcher(threshold=80)
            >>> matcher.find_best_match("Postgres", ["PostgreSQL", "MySQL", "MongoDB"])
            ("PostgreSQL", 90)
        """
        if not candidates:
            return (None, 0)

        best_match = None
        best_score = 0

        for candidate in candidates:
            score = self.similarity(query, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= self.threshold:
            return (best_match, best_score)

        return (None, 0)

    def match_any(self, query: str, candidates: List[str]) -> bool:
        """
        Check if query matches any candidate.

        Args:
            query: Term to search for
            candidates: List of candidate terms

        Returns:
            True if any candidate matches above threshold
        """
        match, score = self.find_best_match(query, candidates)
        return match is not None

    def filter_matches(
        self, queries: List[str], candidates: List[str]
    ) -> List[Tuple[str, str, int]]:
        """
        Find all fuzzy matches between two lists.

        Args:
            queries: List of query terms
            candidates: List of candidate terms

        Returns:
            List of (query, candidate, score) tuples for all matches

        Examples:
            >>> matcher = FuzzyMatcher(threshold=85)
            >>> queries = ["Python", "Postgres"]
            >>> candidates = ["Python 3", "PostgreSQL", "Java"]
            >>> matcher.filter_matches(queries, candidates)
            [("Python", "Python 3", 92), ("Postgres", "PostgreSQL", 90)]
        """
        matches = []

        for query in queries:
            for candidate in candidates:
                score = self.similarity(query, candidate)
                if score >= self.threshold:
                    matches.append((query, candidate, score))

        # Sort by score descending
        matches.sort(key=lambda x: x[2], reverse=True)

        return matches
