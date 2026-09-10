"""
Tree Matching Module
Matches trees using feature similarity
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.spatial.distance import cosine
from .temporal_analyzer import TemporalAnalyzer


class TreeMatcher:
    """
    Matches tree images using feature similarity
    Implements various matching strategies
    """
    
    def __init__(
        self, 
        similarity_threshold: float = 0.75,
        high_confidence_threshold: float = 0.90
    ):
        """
        Initialize tree matcher
        
        Args:
            similarity_threshold: Minimum similarity for a match
            high_confidence_threshold: High confidence match threshold
        """
        self.similarity_threshold = similarity_threshold
        self.high_confidence_threshold = high_confidence_threshold
        self.temporal_analyzer = TemporalAnalyzer()
    
    def calculate_similarity(
        self, 
        features1: np.ndarray, 
        features2: np.ndarray
    ) -> float:
        """
        Calculate similarity between two feature vectors using cosine similarity
        
        Args:
            features1: First feature vector
            features2: Second feature vector
            
        Returns:
            Similarity score (0-1, where 1 is identical)
        """
        try:
            # Ensure numpy arrays
            if not isinstance(features1, np.ndarray):
                features1 = np.array(features1)
            if not isinstance(features2, np.ndarray):
                features2 = np.array(features2)
            
            # Ensure same shape
            if features1.shape != features2.shape:
                return 0.0
            
            # Flatten if needed
            features1 = features1.flatten()
            features2 = features2.flatten()
            if not np.all(np.isfinite(features1)) or not np.all(np.isfinite(features2)):
                return 0.0
            
            # Handle zero vectors
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Cosine similarity: 1 - cosine_distance
            similarity = 1 - cosine(features1, features2)
            
            # Ensure result is in [0, 1]
            similarity = max(0.0, min(1.0, similarity))
            
            return float(similarity)
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_best_match(
        self,
        query_features: np.ndarray,
        database_trees: List[Dict[str, any]]
    ) -> Optional[Dict[str, any]]:
        """
        Find best matching tree in database
        
        Args:
            query_features: Features of query image
            database_trees: List of tree records with 'features' and 'tree_id'
            
        Returns:
            Best match with similarity score or None
        """
        if not database_trees:
            return None
        
        best_match = None
        best_similarity = 0.0
        all_similarities = []
        
        for i, tree in enumerate(database_trees):
            tree_features = tree.get('features')
            
            # Handle different feature formats
            if tree_features is None:
                print(f"    ⚠️  Tree {i+1}: No features")
                continue
            
            # Convert to numpy array if needed
            if not isinstance(tree_features, np.ndarray):
                tree_features = np.array(tree_features)
            
            if len(tree_features) == 0:
                print(f"    ⚠️  Tree {i+1}: Empty features")
                continue
            
            # Check feature shape
            if query_features.shape != tree_features.shape:
                print(f"    ⚠️  Tree {i+1} ({tree.get('tree_id', 'unknown')[:8]}...): Shape mismatch {query_features.shape} vs {tree_features.shape}")
                continue
            
            similarity = self.calculate_similarity(query_features, tree_features)
            all_similarities.append((tree.get('tree_id', 'unknown')[:8], similarity))
            
            print(f"    Tree {i+1} ({tree.get('tree_id', 'unknown')[:8]}...): similarity = {similarity:.3f} ({similarity:.1%})")
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'tree_id': tree.get('tree_id'),
                    'similarity': similarity,
                    'confidence': self._calculate_confidence(similarity),
                    'tree_data': tree
                }
        
        # Print summary
        print(f"\n  📊 Similarity Summary:")
        for tree_id, sim in sorted(all_similarities, key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {tree_id}...: {sim:.3f} ({sim:.1%})")
        print(f"  🎯 Best: {best_similarity:.3f} ({best_similarity:.1%})")
        print(f"  📏 Threshold: {self.similarity_threshold:.3f} ({self.similarity_threshold:.1%})")
        
        # Only return if above threshold
        if best_match and best_match['similarity'] >= self.similarity_threshold:
            print(f"  ✅ Returning match: {best_match['tree_id'][:8]}...")
            return best_match
        else:
            print(f"  ❌ No match above threshold")
        
        return None
    
    def find_all_matches(
        self,
        query_features: np.ndarray,
        database_trees: List[Dict[str, any]],
        top_k: int = 5
    ) -> List[Dict[str, any]]:
        """
        Find top K matching trees
        
        Args:
            query_features: Features of query image
            database_trees: List of tree records
            top_k: Number of top matches to return
            
        Returns:
            List of matches sorted by similarity
        """
        matches = []
        
        for tree in database_trees:
            tree_features = np.array(tree.get('features', []))
            if len(tree_features) == 0:
                continue
            
            similarity = self.calculate_similarity(query_features, tree_features)
            
            if similarity >= self.similarity_threshold:
                matches.append({
                    'tree_id': tree.get('tree_id'),
                    'similarity': similarity,
                    'confidence': self._calculate_confidence(similarity),
                    'tree_data': tree
                })
        
        # Sort by similarity and return top K
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches[:top_k]
    
    def check_duplicate(
        self,
        query_features: np.ndarray,
        database_trees: List[Dict[str, any]],
        duplicate_threshold: float = 0.80
    ) -> Optional[Dict[str, any]]:
        """
        Check if tree already exists in database (duplicate detection)
        
        Args:
            query_features: Features of query image
            database_trees: List of existing trees
            duplicate_threshold: Threshold for duplicate detection (default: 0.80)
            
        Returns:
            Duplicate tree info or None
        """
        if not database_trees:
            print("  ℹ️  No trees in database yet")
            return None
        
        print(f"  🔎 Checking {len(database_trees)} trees for duplicates (threshold: {duplicate_threshold:.2%})")
        
        best_match = None
        best_similarity = 0.0
        
        for i, tree in enumerate(database_trees):
            tree_features = tree.get('features')
            
            # Handle different feature formats
            if tree_features is None:
                print(f"    ⚠️  Tree {i+1}: No features")
                continue
            
            # Convert to numpy array if needed
            if not isinstance(tree_features, np.ndarray):
                tree_features = np.array(tree_features)
            
            if len(tree_features) == 0:
                print(f"    ⚠️  Tree {i+1}: Empty features")
                continue
            
            # Ensure same shape
            if query_features.shape != tree_features.shape:
                print(f"    ⚠️  Tree {i+1}: Shape mismatch {query_features.shape} vs {tree_features.shape}")
                continue
            
            similarity = self.calculate_similarity(query_features, tree_features)
            print(f"    Tree {i+1} ({tree.get('tree_id', 'unknown')[:8]}...): similarity = {similarity:.2%}")
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = tree
            
            # Return immediately if high similarity found
            if similarity >= duplicate_threshold:
                print(f"    ✅ DUPLICATE FOUND! Similarity: {similarity:.2%}")
                return {
                    'tree_id': tree.get('tree_id'),
                    'similarity': float(similarity),
                    'is_duplicate': True,
                    'tree_data': tree
                }
        
        if best_match:
            print(f"  ℹ️  Best match: {best_similarity:.2%} (below threshold {duplicate_threshold:.2%})")
        
        return None
    
    def _calculate_confidence(self, similarity: float) -> str:
        """
        Calculate confidence level based on similarity
        
        Args:
            similarity: Similarity score
            
        Returns:
            Confidence level string
        """
        if similarity >= self.high_confidence_threshold:
            return 'high'
        elif similarity >= self.similarity_threshold:
            return 'medium'
        else:
            return 'low'
