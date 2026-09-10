"""
Database Manager
Handles database operations for tree recognition system
Supports SQLite, PostgreSQL, and MongoDB
"""
import sqlite3
import json
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import pickle

# PostgreSQL support (optional)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    RealDictCursor = None

# MongoDB support (optional)
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, OperationFailure
    from bson.objectid import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    MongoClient = None
    ConnectionFailure = None
    OperationFailure = None
    ObjectId = None


class DatabaseManager:
    """
    Manages database operations for tree recognition system
    Supports SQLite (development), PostgreSQL (production), and MongoDB
    """
    
    def __init__(self, db_type: str = 'sqlite', connection_string: str = None, database_name: str = 'tree_recognition'):
        """
        Initialize database manager
        
        Args:
            db_type: 'sqlite', 'postgresql', or 'mongodb'
            connection_string: Database connection string
            database_name: Database name (for MongoDB)
        """
        self.db_type = db_type.lower()
        self.connection_string = connection_string
        self.database_name = database_name
        self.conn = None
        self.db = None  # For MongoDB
        self._connect()
        self._initialize_schema()
    
    def _connect(self):
        """Establish database connection"""
        try:
            if self.db_type == 'sqlite':
                db_path = self.connection_string or 'data/database/trees.db'
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                self.conn = sqlite3.connect(db_path, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
            elif self.db_type == 'postgresql':
                if not PSYCOPG2_AVAILABLE:
                    raise ImportError("psycopg2 is required for PostgreSQL. Install with: pip install psycopg2-binary")
                self.conn = psycopg2.connect(self.connection_string)
                self.conn.cursor_factory = RealDictCursor
            elif self.db_type == 'mongodb':
                if not MONGODB_AVAILABLE:
                    raise ImportError("pymongo is required for MongoDB. Install with: pip install pymongo")
                
                # MongoDB connection
                connection_str = self.connection_string or 'mongodb://localhost:27017/'
                self.conn = MongoClient(connection_str)
                self.db = self.conn[self.database_name]
                
                # Test connection
                self.conn.admin.command('ping')
                print(f"Successfully connected to MongoDB: {self.database_name}")
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise
    
    def _initialize_schema(self):
        """Initialize database schema"""
        # For SQLite, always use _create_basic_tables for reliability
        if self.db_type == 'sqlite':
            self._create_basic_tables()
            return
        
        # For MongoDB, create indexes
        if self.db_type == 'mongodb':
            self._create_mongodb_indexes()
            return
        
        # For PostgreSQL, try to load schema file
        schema_path = os.path.join(
            os.path.dirname(__file__),
            'schema.sql'
        )
        
        try:
            if not os.path.exists(schema_path):
                print(f"Warning: Schema file not found: {schema_path}")
                return
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Execute schema
            cursor = self.conn.cursor()
            
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            for statement in statements:
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        # Ignore errors for existing tables/indexes
                        if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                            print(f"Schema execution warning: {e}")
            
            self.conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Error initializing schema: {e}")
    
    def _create_mongodb_indexes(self):
        """Create indexes for MongoDB collections"""
        try:
            # Trees collection indexes
            self.db.trees.create_index('tree_id', unique=True)
            self.db.trees.create_index('tree_type')
            self.db.trees.create_index('tree_species')
            self.db.trees.create_index('status')
            self.db.trees.create_index('registered_date')
            self.db.trees.create_index([('location_lat', 1), ('location_lng', 1)])
            
            # Tree features indexes
            self.db.tree_features.create_index('tree_id')
            self.db.tree_features.create_index('extraction_date')
            
            # Tree images indexes
            self.db.tree_images.create_index('tree_id')
            self.db.tree_images.create_index('uploaded_date')
            
            # Tree observations indexes
            self.db.tree_observations.create_index('tree_id')
            self.db.tree_observations.create_index('observation_date')
            
            print("MongoDB indexes created successfully")
        except Exception as e:
            print(f"Error creating MongoDB indexes: {e}")
    
    def _create_basic_tables(self):
        """Create basic tables for SQLite"""
        try:
            # Enable foreign keys for SQLite
            if self.db_type == 'sqlite':
                self.conn.execute("PRAGMA foreign_keys = ON")
            
            cursor = self.conn.cursor()
            
            # Trees table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trees (
                    tree_id TEXT PRIMARY KEY,
                    tree_type TEXT,
                    tree_species TEXT,
                    location_lat REAL,
                    location_lng REAL,
                    location_address TEXT,
                    metadata TEXT,
                    registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Tree features table - without FOREIGN KEY to avoid issues
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tree_features (
                    tree_id TEXT NOT NULL,
                    features BLOB,
                    feature_vector TEXT,
                    image_path TEXT,
                    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tree_id, extraction_date)
                )
            """)
            
            # Tree images table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tree_images (
                    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tree_id TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    image_type TEXT DEFAULT 'registration',
                    uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tree observations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tree_observations (
                    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tree_id TEXT NOT NULL,
                    features BLOB,
                    feature_vector TEXT,
                    image_path TEXT,
                    health_status TEXT,
                    growth_stage TEXT,
                    notes TEXT,
                    observation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trees_tree_id ON trees(tree_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tree_features_tree_id ON tree_features(tree_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tree_images_tree_id ON tree_images(tree_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tree_observations_tree_id ON tree_observations(tree_id)")
            
            self.conn.commit()
            cursor.close()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating basic tables: {e}")
            import traceback
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
    
    def _execute_query(self, query: str, params: tuple = None):
        """Execute query with proper parameter style"""
        cursor = self.conn.cursor()
        try:
            if self.db_type == 'sqlite':
                # SQLite uses ? placeholders
                query = query.replace('%s', '?')
                cursor.execute(query, params or ())
            else:
                # PostgreSQL uses %s placeholders
                cursor.execute(query, params or ())
            return cursor
        except Exception as e:
            print(f"Query error: {e}")
            raise
    
    def add_tree(
        self,
        tree_id: str,
        tree_type: str = None,
        location_lat: float = None,
        location_lng: float = None,
        location_address: str = None,
        features: np.ndarray = None,
        image_path: str = None,
        metadata: Dict = None
    ) -> bool:
        """Add a new tree to database"""
        try:
            # MongoDB implementation
            if self.db_type == 'mongodb':
                # Convert features
                features_list = None
                if features is not None:
                    features_list = features.tolist() if isinstance(features, np.ndarray) else features
                
                # Insert or update tree document
                tree_doc = {
                    'tree_id': tree_id,
                    'tree_type': tree_type,
                    'location_lat': location_lat,
                    'location_lng': location_lng,
                    'location_address': location_address,
                    'metadata': metadata or {},
                    'registered_date': datetime.now(),
                    'last_updated': datetime.now(),
                    'status': 'active'
                }
                
                self.db.trees.update_one(
                    {'tree_id': tree_id},
                    {'$set': tree_doc},
                    upsert=True
                )
                
                # Insert features if provided
                if features is not None:
                    feature_doc = {
                        'tree_id': tree_id,
                        'features': features_list,
                        'image_path': image_path,
                        'extraction_date': datetime.now()
                    }
                    self.db.tree_features.insert_one(feature_doc)
                
                # Insert image if provided
                if image_path:
                    image_doc = {
                        'tree_id': tree_id,
                        'image_path': image_path,
                        'image_type': 'registration',
                        'uploaded_date': datetime.now()
                    }
                    self.db.tree_images.insert_one(image_doc)
                
                return True
            
            # SQL implementation (SQLite/PostgreSQL)
            cursor = self.conn.cursor()
            
            # Convert features
            features_json = None
            features_blob = None
            if features is not None:
                features_list = features.tolist() if isinstance(features, np.ndarray) else features
                features_json = json.dumps(features_list)
                features_blob = pickle.dumps(features) if isinstance(features, np.ndarray) else features
            
            # Insert into trees table
            if self.db_type == 'sqlite':
                cursor.execute("""
                    INSERT OR REPLACE INTO trees 
                    (tree_id, tree_type, location_lat, location_lng, location_address, metadata, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    tree_id,
                    tree_type,
                    location_lat,
                    location_lng,
                    location_address,
                    json.dumps(metadata) if metadata else None
                ))
            else:
                cursor.execute("""
                    INSERT INTO trees 
                    (tree_id, tree_type, location_lat, location_lng, location_address, metadata, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT(tree_id) DO UPDATE SET
                        tree_type = EXCLUDED.tree_type,
                        location_lat = EXCLUDED.location_lat,
                        location_lng = EXCLUDED.location_lng,
                        location_address = EXCLUDED.location_address,
                        last_updated = CURRENT_TIMESTAMP,
                        metadata = EXCLUDED.metadata
                """, (
                    tree_id,
                    tree_type,
                    location_lat,
                    location_lng,
                    location_address,
                    json.dumps(metadata) if metadata else None
                ))
            
            # Insert features if provided
            if features is not None:
                if self.db_type == 'sqlite':
                    cursor.execute("""
                        INSERT INTO tree_features (tree_id, features, feature_vector, image_path)
                        VALUES (?, ?, ?, ?)
                    """, (tree_id, features_blob, features_json, image_path))
                else:
                    cursor.execute("""
                        INSERT INTO tree_features (tree_id, features, feature_vector, image_path)
                        VALUES (%s, %s, %s, %s)
                    """, (tree_id, features_blob, features_json, image_path))
            
            # Insert image if provided
            if image_path:
                if self.db_type == 'sqlite':
                    cursor.execute("""
                        INSERT INTO tree_images (tree_id, image_path, image_type)
                        VALUES (?, ?, ?)
                    """, (tree_id, image_path, 'registration'))
                else:
                    cursor.execute("""
                        INSERT INTO tree_images (tree_id, image_path, image_type)
                        VALUES (%s, %s, %s)
                    """, (tree_id, image_path, 'registration'))
            
            self.conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error adding tree: {e}")
            if self.db_type != 'mongodb':
                self.conn.rollback()
            return False
    
    def get_tree(self, tree_id: str) -> Optional[Dict[str, Any]]:
        """Get tree by ID"""
        try:
            # MongoDB implementation
            if self.db_type == 'mongodb':
                tree = self.db.trees.find_one({'tree_id': tree_id})
                if tree:
                    # Convert ObjectId to string for JSON serialization
                    if '_id' in tree:
                        tree['_id'] = str(tree['_id'])
                    return tree
                return None
            
            # SQL implementation
            if self.db_type == 'sqlite':
                cursor = self.conn.execute("SELECT * FROM trees WHERE tree_id = ?", (tree_id,))
            else:
                cursor = self._execute_query("SELECT * FROM trees WHERE tree_id = %s", (tree_id,))
            
            row = cursor.fetchone()
            if cursor:
                cursor.close()
            
            if row:
                return dict(row) if hasattr(row, 'keys') else row
            return None
            
        except Exception as e:
            print(f"Error getting tree: {e}")
            return None
    
    def get_tree_features(self, tree_id: str) -> Optional[np.ndarray]:
        """Get tree features"""
        try:
            # MongoDB implementation
            if self.db_type == 'mongodb':
                feature = self.db.tree_features.find_one(
                    {'tree_id': tree_id},
                    sort=[('extraction_date', -1)]
                )
                if feature and 'features' in feature:
                    return np.array(feature['features'])
                return None
            
            # SQL implementation
            if self.db_type == 'sqlite':
                cursor = self.conn.execute("""
                    SELECT feature_vector, features FROM tree_features 
                    WHERE tree_id = ? 
                    ORDER BY extraction_date DESC 
                    LIMIT 1
                """, (tree_id,))
            else:
                cursor = self._execute_query("""
                    SELECT feature_vector, features FROM tree_features 
                    WHERE tree_id = %s 
                    ORDER BY extraction_date DESC 
                    LIMIT 1
                """, (tree_id,))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                # Try to get from feature_vector (JSON) first
                if row[0]:
                    try:
                        features_list = json.loads(row[0])
                        return np.array(features_list)
                    except:
                        pass
                
                # Fallback to binary features
                if len(row) > 1 and row[1]:
                    try:
                        return pickle.loads(row[1])
                    except:
                        pass
            
            return None
            
        except Exception as e:
            print(f"Error getting tree features: {e}")
            return None
    
    def get_all_trees(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all trees with pagination"""
        try:
            # MongoDB implementation
            if self.db_type == 'mongodb':
                trees = list(self.db.trees.find(
                    {'$or': [{'status': 'active'}, {'status': {'$exists': False}}]}
                ).sort('registered_date', -1).skip(offset).limit(limit))
                
                # Convert ObjectId to string
                for tree in trees:
                    if '_id' in tree:
                        tree['_id'] = str(tree['_id'])
                return trees
            
            # SQL implementation
            if self.db_type == 'sqlite':
                cursor = self.conn.execute("""
                    SELECT * FROM trees 
                    WHERE status = 'active' OR status IS NULL
                    ORDER BY registered_date DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor = self._execute_query("""
                    SELECT * FROM trees 
                    WHERE status = 'active' OR status IS NULL
                    ORDER BY registered_date DESC 
                    LIMIT %s OFFSET %s
                """, (limit, offset))
            
            rows = cursor.fetchall()
            cursor.close()
            
            return [dict(row) if hasattr(row, 'keys') else row for row in rows]
            
        except Exception as e:
            print(f"Error getting all trees: {e}")
            return []
    
    def get_all_trees_with_features(self) -> List[Dict[str, Any]]:
        """Get all trees with their features for matching"""
        try:
            # MongoDB implementation (optimized with aggregation)
            if self.db_type == 'mongodb':
                pipeline = [
                    {'$match': {'$or': [{'status': 'active'}, {'status': {'$exists': False}}]}},
                    {'$lookup': {
                        'from': 'tree_features',
                        'localField': 'tree_id',
                        'foreignField': 'tree_id',
                        'as': 'features_data'
                    }},
                    {'$unwind': {'path': '$features_data', 'preserveNullAndEmptyArrays': False}},
                    {'$sort': {'features_data.extraction_date': -1}},
                    {'$group': {
                        '_id': '$tree_id',
                        'tree_id': {'$first': '$tree_id'},
                        'tree_type': {'$first': '$tree_type'},
                        'registered_date': {'$first': '$registered_date'},
                        'location_lat': {'$first': '$location_lat'},
                        'location_lng': {'$first': '$location_lng'},
                        'features': {'$first': '$features_data.features'}
                    }}
                ]
                
                results = list(self.db.trees.aggregate(pipeline))
                
                # Convert features to numpy arrays
                for result in results:
                    if 'features' in result and result['features']:
                        result['features'] = np.array(result['features'])
                
                return results
            
            # SQL implementation
            trees = self.get_all_trees(limit=10000)
            result = []
            
            for tree in trees:
                tree_id = tree.get('tree_id') or tree[0] if isinstance(tree, tuple) else None
                if not tree_id:
                    continue
                    
                features = self.get_tree_features(tree_id)
                
                if features is not None:
                    result.append({
                        'tree_id': tree_id,
                        'tree_type': tree.get('tree_type') if isinstance(tree, dict) else None,
                        'features': features,
                        'registered_date': tree.get('registered_date') if isinstance(tree, dict) else None,
                        'location_lat': tree.get('location_lat') if isinstance(tree, dict) else None,
                        'location_lng': tree.get('location_lng') if isinstance(tree, dict) else None
                    })
            
            return result
            
        except Exception as e:
            print(f"Error getting trees with features: {e}")
            return []
    
    def add_observation(
        self,
        tree_id: str,
        features: np.ndarray,
        image_path: str = None,
        health_status: str = None,
        growth_stage: str = None,
        notes: str = None
    ) -> bool:
        """Add temporal observation for a tree"""
        try:
            # MongoDB implementation
            if self.db_type == 'mongodb':
                features_list = features.tolist() if isinstance(features, np.ndarray) else features
                
                observation_doc = {
                    'tree_id': tree_id,
                    'features': features_list,
                    'image_path': image_path,
                    'health_status': health_status,
                    'growth_stage': growth_stage,
                    'notes': notes,
                    'observation_date': datetime.now()
                }
                
                self.db.tree_observations.insert_one(observation_doc)
                return True
            
            # SQL implementation
            cursor = self.conn.cursor()
            
            features_list = features.tolist() if isinstance(features, np.ndarray) else features
            features_json = json.dumps(features_list)
            features_blob = pickle.dumps(features) if isinstance(features, np.ndarray) else features
            
            if self.db_type == 'sqlite':
                cursor.execute("""
                    INSERT INTO tree_observations 
                    (tree_id, features, feature_vector, image_path, health_status, growth_stage, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tree_id,
                    features_blob,
                    features_json,
                    image_path,
                    health_status,
                    growth_stage,
                    notes
                ))
            else:
                cursor.execute("""
                    INSERT INTO tree_observations 
                    (tree_id, features, feature_vector, image_path, health_status, growth_stage, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    tree_id,
                    features_blob,
                    features_json,
                    image_path,
                    health_status,
                    growth_stage,
                    notes
                ))
            
            self.conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error adding observation: {e}")
            if self.db_type != 'mongodb':
                self.conn.rollback()
            return False
    
    def get_observations(
        self,
        tree_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get temporal observations for a tree"""
        try:
            # MongoDB implementation
            if self.db_type == 'mongodb':
                observations = list(self.db.tree_observations.find(
                    {'tree_id': tree_id}
                ).sort('observation_date', -1).limit(limit))
                
                # Convert features and ObjectId
                for obs in observations:
                    if '_id' in obs:
                        obs['_id'] = str(obs['_id'])
                    if 'features' in obs:
                        obs['features'] = np.array(obs['features'])
                
                return observations
            
            # SQL implementation
            if self.db_type == 'sqlite':
                cursor = self.conn.execute("""
                    SELECT * FROM tree_observations 
                    WHERE tree_id = ? 
                    ORDER BY observation_date DESC 
                    LIMIT ?
                """, (tree_id, limit))
            else:
                cursor = self._execute_query("""
                    SELECT * FROM tree_observations 
                    WHERE tree_id = %s 
                    ORDER BY observation_date DESC 
                    LIMIT %s
                """, (tree_id, limit))
            
            rows = cursor.fetchall()
            cursor.close()
            
            observations = []
            for row in rows:
                obs = dict(row) if hasattr(row, 'keys') else row
                # Load features
                if isinstance(obs, dict) and obs.get('feature_vector'):
                    try:
                        obs['features'] = np.array(json.loads(obs['feature_vector']))
                    except:
                        pass
                observations.append(obs)
            
            return observations
            
        except Exception as e:
            print(f"Error getting observations: {e}")
            return []
    
    def delete_tree(self, tree_id: str) -> bool:
        """Delete a tree and all related data"""
        try:
            # MongoDB implementation
            if self.db_type == 'mongodb':
                # Delete tree and all related data
                self.db.trees.delete_one({'tree_id': tree_id})
                self.db.tree_features.delete_many({'tree_id': tree_id})
                self.db.tree_images.delete_many({'tree_id': tree_id})
                self.db.tree_observations.delete_many({'tree_id': tree_id})
                return True
            
            # SQL implementation
            if self.db_type == 'sqlite':
                cursor = self.conn.execute("DELETE FROM trees WHERE tree_id = ?", (tree_id,))
            else:
                cursor = self._execute_query("DELETE FROM trees WHERE tree_id = %s", (tree_id,))
            
            self.conn.commit()
            if hasattr(cursor, 'close'):
                cursor.close()
            return True
            
        except Exception as e:
            print(f"Error deleting tree: {e}")
            if self.db_type != 'mongodb':
                self.conn.rollback()
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()