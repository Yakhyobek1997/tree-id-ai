"""
Tree Recognition Models
"""
try:
    from .feature_extractor import FeatureExtractor, MultiViewFeatureExtractor
except ImportError as e:
    print(f"Warning: Could not import FeatureExtractor: {e}")
    # Create a simple fallback
    from .feature_extractor import FeatureExtractor

from .temporal_analyzer import TemporalAnalyzer
from .tree_matcher import TreeMatcher

__all__ = ['FeatureExtractor', 'TemporalAnalyzer', 'TreeMatcher']
