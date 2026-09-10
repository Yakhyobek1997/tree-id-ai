"""
Migration Script: SQLite to MongoDB
Migrates all data from SQLite database to MongoDB
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database.db_manager import DatabaseManager
from backend.utils.mongo_config import MongoConfig
import numpy as np
from typing import Dict, List
import argparse


class DatabaseMigration:
    """Handles migration from SQLite to MongoDB"""
    
    def __init__(
        self,
        sqlite_path: str = 'data/database/trees.db',
        mongo_connection: str = 'mongodb://localhost:27017/',
        mongo_database: str = 'tree_recognition'
    ):
        """
        Initialize migration
        
        Args:
            sqlite_path: Path to SQLite database
            mongo_connection: MongoDB connection string
            mongo_database: MongoDB database name
        """
        print("=" * 60)
        print("Database Migration: SQLite → MongoDB")
        print("=" * 60)
        
        # Connect to databases
        print(f"\nConnecting to SQLite: {sqlite_path}")
        self.sqlite_db = DatabaseManager(
            db_type='sqlite',
            connection_string=sqlite_path
        )
        
        print(f"Connecting to MongoDB: {mongo_database}")
        self.mongo_db = DatabaseManager(
            db_type='mongodb',
            connection_string=mongo_connection,
            database_name=mongo_database
        )
        
        self.stats = {
            'trees_total': 0,
            'trees_migrated': 0,
            'features_migrated': 0,
            'observations_migrated': 0,
            'errors': []
        }
    
    def migrate_trees(self, limit: int = None) -> Dict:
        """
        Migrate all trees from SQLite to MongoDB
        
        Args:
            limit: Maximum number of trees to migrate (None = all)
        
        Returns:
            Migration statistics
        """
        print("\n" + "-" * 60)
        print("Migrating Trees...")
        print("-" * 60)
        
        # Get all trees from SQLite
        trees = self.sqlite_db.get_all_trees(limit=limit or 10000)
        self.stats['trees_total'] = len(trees)
        
        print(f"Found {len(trees)} trees in SQLite database")
        
        for i, tree in enumerate(trees, 1):
            tree_id = tree.get('tree_id')
            if not tree_id:
                print(f"  ⚠️  Skipping tree {i}: No tree_id")
                continue
            
            try:
                # Get features from SQLite
                features = self.sqlite_db.get_tree_features(tree_id)
                
                # Migrate tree to MongoDB
                success = self.mongo_db.add_tree(
                    tree_id=tree_id,
                    tree_type=tree.get('tree_type'),
                    location_lat=tree.get('location_lat'),
                    location_lng=tree.get('location_lng'),
                    location_address=tree.get('location_address'),
                    features=features,
                    metadata={}
                )
                
                if success:
                    self.stats['trees_migrated'] += 1
                    if features is not None:
                        self.stats['features_migrated'] += 1
                    
                    # Progress indicator
                    if i % 10 == 0 or i == len(trees):
                        print(f"  Progress: {i}/{len(trees)} trees migrated")
                else:
                    error = f"Failed to migrate tree: {tree_id}"
                    self.stats['errors'].append(error)
                    print(f"  ❌ {error}")
                
            except Exception as e:
                error = f"Error migrating tree {tree_id}: {e}"
                self.stats['errors'].append(error)
                print(f"  ❌ {error}")
        
        print(f"\n✅ Trees migrated: {self.stats['trees_migrated']}/{self.stats['trees_total']}")
        print(f"✅ Features migrated: {self.stats['features_migrated']}")
        
        return self.stats
    
    def migrate_observations(self, tree_id: str = None) -> int:
        """
        Migrate observations for trees
        
        Args:
            tree_id: Specific tree ID (None = all trees)
        
        Returns:
            Number of observations migrated
        """
        print("\n" + "-" * 60)
        print("Migrating Observations...")
        print("-" * 60)
        
        if tree_id:
            tree_ids = [tree_id]
        else:
            trees = self.mongo_db.get_all_trees(limit=10000)
            tree_ids = [t.get('tree_id') for t in trees if t.get('tree_id')]
        
        observations_count = 0
        
        for tid in tree_ids:
            try:
                # Get observations from SQLite
                observations = self.sqlite_db.get_observations(tid)
                
                for obs in observations:
                    features = obs.get('features')
                    if features is None and obs.get('feature_vector'):
                        # Try to reconstruct features from JSON
                        import json
                        try:
                            features = np.array(json.loads(obs['feature_vector']))
                        except:
                            pass
                    
                    if features is not None:
                        # Add observation to MongoDB
                        success = self.mongo_db.add_observation(
                            tree_id=tid,
                            features=features,
                            image_path=obs.get('image_path'),
                            health_status=obs.get('health_status'),
                            growth_stage=obs.get('growth_stage'),
                            notes=obs.get('notes')
                        )
                        
                        if success:
                            observations_count += 1
            
            except Exception as e:
                error = f"Error migrating observations for {tid}: {e}"
                self.stats['errors'].append(error)
                print(f"  ❌ {error}")
        
        self.stats['observations_migrated'] = observations_count
        print(f"\n✅ Observations migrated: {observations_count}")
        
        return observations_count
    
    def verify_migration(self) -> bool:
        """
        Verify that migration was successful
        
        Returns:
            True if verification passed
        """
        print("\n" + "-" * 60)
        print("Verifying Migration...")
        print("-" * 60)
        
        # Compare counts
        sqlite_trees = len(self.sqlite_db.get_all_trees(limit=10000))
        mongo_trees = len(self.mongo_db.get_all_trees(limit=10000))
        
        print(f"SQLite trees: {sqlite_trees}")
        print(f"MongoDB trees: {mongo_trees}")
        
        if sqlite_trees == mongo_trees:
            print("✅ Tree count matches!")
            return True
        else:
            print("⚠️  Tree count mismatch!")
            return False
    
    def print_summary(self):
        """Print migration summary"""
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"Trees found:      {self.stats['trees_total']}")
        print(f"Trees migrated:   {self.stats['trees_migrated']}")
        print(f"Features:         {self.stats['features_migrated']}")
        print(f"Observations:     {self.stats['observations_migrated']}")
        print(f"Errors:           {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\nErrors:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        print("=" * 60)
    
    def close(self):
        """Close database connections"""
        self.sqlite_db.close()
        self.mongo_db.close()


def main():
    """Main migration script"""
    parser = argparse.ArgumentParser(description='Migrate SQLite database to MongoDB')
    parser.add_argument(
        '--sqlite-path',
        default='data/database/trees.db',
        help='Path to SQLite database (default: data/database/trees.db)'
    )
    parser.add_argument(
        '--mongo-host',
        default='localhost',
        help='MongoDB host (default: localhost)'
    )
    parser.add_argument(
        '--mongo-port',
        type=int,
        default=27017,
        help='MongoDB port (default: 27017)'
    )
    parser.add_argument(
        '--mongo-database',
        default='tree_recognition',
        help='MongoDB database name (default: tree_recognition)'
    )
    parser.add_argument(
        '--mongo-connection',
        help='Full MongoDB connection string (overrides host/port)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of trees to migrate (for testing)'
    )
    parser.add_argument(
        '--skip-observations',
        action='store_true',
        help='Skip migrating observations'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify migration after completion'
    )
    
    args = parser.parse_args()
    
    # Build MongoDB connection string
    if args.mongo_connection:
        mongo_connection = args.mongo_connection
    else:
        mongo_connection = f'mongodb://{args.mongo_host}:{args.mongo_port}/'
    
    # Create migration instance
    migration = DatabaseMigration(
        sqlite_path=args.sqlite_path,
        mongo_connection=mongo_connection,
        mongo_database=args.mongo_database
    )
    
    try:
        # Migrate trees
        migration.migrate_trees(limit=args.limit)
        
        # Migrate observations
        if not args.skip_observations:
            migration.migrate_observations()
        
        # Verify if requested
        if args.verify:
            migration.verify_migration()
        
        # Print summary
        migration.print_summary()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        migration.close()
    
    print("\n✅ Migration complete!")


if __name__ == '__main__':
    main()


