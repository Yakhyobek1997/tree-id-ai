"""
MongoDB Database Test
Tests MongoDB integration with DatabaseManager
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.db_manager import DatabaseManager
from backend.utils.mongo_config import MongoConfig
import numpy as np
from datetime import datetime


def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n" + "=" * 60)
    print("Test 1: MongoDB Connection")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        print("✅ MongoDB connection successful!")
        db.close()
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False


def test_add_tree():
    """Test adding a tree"""
    print("\n" + "=" * 60)
    print("Test 2: Add Tree")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Create test data
        tree_id = f"test-tree-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        features = np.random.rand(256).astype(np.float32)
        
        # Add tree
        success = db.add_tree(
            tree_id=tree_id,
            tree_type='Terak',
            location_lat=41.311151,
            location_lng=69.279737,
            location_address='Toshkent, O\'zbekiston',
            features=features,
            image_path='test/image.jpg',
            metadata={'age': 10, 'height': 15.5, 'test': True}
        )
        
        if success:
            print(f"✅ Tree added successfully: {tree_id}")
            db.close()
            return tree_id
        else:
            print("❌ Failed to add tree")
            db.close()
            return None
    
    except Exception as e:
        print(f"❌ Error adding tree: {e}")
        return None


def test_get_tree(tree_id: str):
    """Test getting a tree"""
    print("\n" + "=" * 60)
    print("Test 3: Get Tree")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Get tree
        tree = db.get_tree(tree_id)
        
        if tree:
            print(f"✅ Tree retrieved successfully!")
            print(f"   Tree ID: {tree.get('tree_id')}")
            print(f"   Type: {tree.get('tree_type')}")
            print(f"   Location: ({tree.get('location_lat')}, {tree.get('location_lng')})")
            print(f"   Metadata: {tree.get('metadata')}")
            db.close()
            return True
        else:
            print(f"❌ Tree not found: {tree_id}")
            db.close()
            return False
    
    except Exception as e:
        print(f"❌ Error getting tree: {e}")
        return False


def test_get_features(tree_id: str):
    """Test getting tree features"""
    print("\n" + "=" * 60)
    print("Test 4: Get Features")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Get features
        features = db.get_tree_features(tree_id)
        
        if features is not None:
            print(f"✅ Features retrieved successfully!")
            print(f"   Shape: {features.shape}")
            print(f"   Type: {features.dtype}")
            print(f"   First 5 values: {features[:5]}")
            db.close()
            return True
        else:
            print(f"❌ Features not found")
            db.close()
            return False
    
    except Exception as e:
        print(f"❌ Error getting features: {e}")
        return False


def test_add_observation(tree_id: str):
    """Test adding an observation"""
    print("\n" + "=" * 60)
    print("Test 5: Add Observation")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Add observation
        features = np.random.rand(256).astype(np.float32)
        success = db.add_observation(
            tree_id=tree_id,
            features=features,
            image_path='test/observation.jpg',
            health_status='healthy',
            growth_stage='mature',
            notes='Test observation'
        )
        
        if success:
            print(f"✅ Observation added successfully!")
            db.close()
            return True
        else:
            print("❌ Failed to add observation")
            db.close()
            return False
    
    except Exception as e:
        print(f"❌ Error adding observation: {e}")
        return False


def test_get_observations(tree_id: str):
    """Test getting observations"""
    print("\n" + "=" * 60)
    print("Test 6: Get Observations")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Get observations
        observations = db.get_observations(tree_id)
        
        print(f"✅ Observations retrieved: {len(observations)}")
        for i, obs in enumerate(observations, 1):
            print(f"   Observation {i}:")
            print(f"      Health: {obs.get('health_status')}")
            print(f"      Growth Stage: {obs.get('growth_stage')}")
            print(f"      Notes: {obs.get('notes')}")
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Error getting observations: {e}")
        return False


def test_get_all_trees():
    """Test getting all trees"""
    print("\n" + "=" * 60)
    print("Test 7: Get All Trees")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Get all trees
        trees = db.get_all_trees(limit=100)
        
        print(f"✅ Retrieved {len(trees)} trees")
        for i, tree in enumerate(trees[:5], 1):  # Show first 5
            print(f"   {i}. {tree.get('tree_id')} - {tree.get('tree_type')}")
        
        if len(trees) > 5:
            print(f"   ... and {len(trees) - 5} more")
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Error getting all trees: {e}")
        return False


def test_get_all_trees_with_features():
    """Test getting all trees with features"""
    print("\n" + "=" * 60)
    print("Test 8: Get All Trees with Features")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Get all trees with features
        trees = db.get_all_trees_with_features()
        
        print(f"✅ Retrieved {len(trees)} trees with features")
        for i, tree in enumerate(trees[:3], 1):  # Show first 3
            print(f"   {i}. {tree.get('tree_id')}")
            print(f"      Features shape: {tree.get('features').shape if tree.get('features') is not None else 'None'}")
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Error getting trees with features: {e}")
        return False


def test_delete_tree(tree_id: str):
    """Test deleting a tree"""
    print("\n" + "=" * 60)
    print("Test 9: Delete Tree")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Delete tree
        success = db.delete_tree(tree_id)
        
        if success:
            print(f"✅ Tree deleted successfully: {tree_id}")
            
            # Verify deletion
            tree = db.get_tree(tree_id)
            if tree is None:
                print("✅ Deletion verified!")
            else:
                print("⚠️  Tree still exists after deletion")
            
            db.close()
            return True
        else:
            print("❌ Failed to delete tree")
            db.close()
            return False
    
    except Exception as e:
        print(f"❌ Error deleting tree: {e}")
        return False


def cleanup_test_database():
    """Clean up test database"""
    print("\n" + "=" * 60)
    print("Cleanup: Removing Test Database")
    print("=" * 60)
    
    try:
        db = DatabaseManager(
            db_type='mongodb',
            connection_string='mongodb://localhost:27017/',
            database_name='tree_recognition_test'
        )
        
        # Drop test database
        db.conn.drop_database('tree_recognition_test')
        print("✅ Test database removed")
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print(" " * 20 + "MONGODB TEST SUITE")
    print("=" * 70)
    
    results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    # Test 1: Connection
    if test_mongodb_connection():
        results['passed'] += 1
    else:
        results['failed'] += 1
        print("\n⚠️  Cannot continue without MongoDB connection")
        return results
    results['total'] += 1
    
    # Test 2: Add tree
    tree_id = test_add_tree()
    if tree_id:
        results['passed'] += 1
    else:
        results['failed'] += 1
        print("\n⚠️  Cannot continue without adding a tree")
        return results
    results['total'] += 1
    
    # Test 3: Get tree
    if test_get_tree(tree_id):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1
    
    # Test 4: Get features
    if test_get_features(tree_id):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1
    
    # Test 5: Add observation
    if test_add_observation(tree_id):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1
    
    # Test 6: Get observations
    if test_get_observations(tree_id):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1
    
    # Test 7: Get all trees
    if test_get_all_trees():
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1
    
    # Test 8: Get all trees with features
    if test_get_all_trees_with_features():
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1
    
    # Test 9: Delete tree
    if test_delete_tree(tree_id):
        results['passed'] += 1
    else:
        results['failed'] += 1
    results['total'] += 1
    
    # Cleanup
    cleanup_test_database()
    
    # Print summary
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests:  {results['total']}")
    print(f"Passed:       {results['passed']} ✅")
    print(f"Failed:       {results['failed']} {'❌' if results['failed'] > 0 else ''}")
    print(f"Success Rate: {results['passed']/results['total']*100:.1f}%")
    print("=" * 70)
    
    return results


if __name__ == '__main__':
    results = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)


