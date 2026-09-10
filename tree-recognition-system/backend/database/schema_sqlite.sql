-- SQLite Schema for Tree Recognition System
-- Compatible with backend/database/db_manager.py

-- ===== TREES TABLE =====
CREATE TABLE IF NOT EXISTS trees (
    tree_id TEXT PRIMARY KEY,
    tree_type TEXT,
    tree_species TEXT,
    location_lat REAL,
    location_lng REAL,
    location_address TEXT,
    metadata TEXT,  -- JSON string
    registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);

-- ===== TREE FEATURES TABLE =====
CREATE TABLE IF NOT EXISTS tree_features (
    tree_id TEXT NOT NULL,
    features BLOB,  -- Pickled numpy array
    feature_vector TEXT,  -- JSON string
    image_path TEXT,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tree_id) REFERENCES trees(tree_id) ON DELETE CASCADE,
    PRIMARY KEY (tree_id, extraction_date)
);

-- ===== TREE IMAGES TABLE =====
CREATE TABLE IF NOT EXISTS tree_images (
    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tree_id TEXT NOT NULL,
    image_path TEXT NOT NULL,
    image_type TEXT DEFAULT 'registration',
    uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tree_id) REFERENCES trees(tree_id) ON DELETE CASCADE
);

-- ===== TREE OBSERVATIONS TABLE =====
CREATE TABLE IF NOT EXISTS tree_observations (
    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tree_id TEXT NOT NULL,
    features BLOB,  -- Pickled numpy array
    feature_vector TEXT,  -- JSON string
    image_path TEXT,
    health_status TEXT,
    growth_stage TEXT,
    notes TEXT,
    observation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tree_id) REFERENCES trees(tree_id) ON DELETE CASCADE
);

-- ===== INDEXES =====
CREATE INDEX IF NOT EXISTS idx_trees_tree_id ON trees(tree_id);
CREATE INDEX IF NOT EXISTS idx_trees_tree_type ON trees(tree_type);
CREATE INDEX IF NOT EXISTS idx_trees_status ON trees(status);
CREATE INDEX IF NOT EXISTS idx_tree_features_tree_id ON tree_features(tree_id);
CREATE INDEX IF NOT EXISTS idx_tree_images_tree_id ON tree_images(tree_id);
CREATE INDEX IF NOT EXISTS idx_tree_observations_tree_id ON tree_observations(tree_id);
CREATE INDEX IF NOT EXISTS idx_tree_observations_date ON tree_observations(observation_date DESC);


