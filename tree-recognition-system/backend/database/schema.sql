-- backend/database/schema.sql

-- ===== EXTENSIONS =====
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===== TREES TABLE =====
CREATE TABLE IF NOT EXISTS trees (
    tree_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tree_species VARCHAR(100),
    first_seen TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP,
    total_scans INTEGER DEFAULT 1,
    gps_location GEOGRAPHY(POINT) DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ===== TREE SCANS TABLE =====
CREATE TABLE IF NOT EXISTS tree_scans (
    scan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tree_id UUID REFERENCES trees(tree_id) ON DELETE CASCADE,
    scan_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Feature vectors
    global_features VECTOR(1024),
    multiscale_features VECTOR(2560),
    color_histogram VECTOR(288),
    texture_features VECTOR(59),
    
    -- Measurements
    area FLOAT,
    perimeter FLOAT,
    branch_count INTEGER,
    
    -- Analysis results
    detected_season VARCHAR(20),
    health_score FLOAT,
    
    -- Images
    image_path TEXT NOT NULL,
    thumbnail_path TEXT,
    
    -- Raw features (full JSON)
    raw_features JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ===== TEMPORAL CHANGES TABLE =====
CREATE TABLE IF NOT EXISTS tree_changes (
    change_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tree_id UUID REFERENCES trees(tree_id) ON DELETE CASCADE,
    scan_from UUID REFERENCES tree_scans(scan_id),
    scan_to UUID REFERENCES tree_scans(scan_id),
    
    time_difference_days INTEGER,
    
    area_change_percent FLOAT,
    branch_change INTEGER,
    color_change_magnitude FLOAT,
    
    is_pruning_event BOOLEAN DEFAULT FALSE,
    is_seasonal_change BOOLEAN DEFAULT FALSE,
    
    change_summary TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ===== SIMILARITY MATCHES TABLE =====
CREATE TABLE IF NOT EXISTS similarity_matches (
    match_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_scan_id UUID REFERENCES tree_scans(scan_id),
    matched_tree_id UUID REFERENCES trees(tree_id),
    
    similarity_score FLOAT,
    is_same_tree BOOLEAN,
    confidence FLOAT,
    
    match_breakdown JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- ===== INDEXES =====
CREATE INDEX IF NOT EXISTS idx_tree_scans_tree_id ON tree_scans(tree_id);
CREATE INDEX IF NOT EXISTS idx_tree_scans_time ON tree_scans(scan_time DESC);
CREATE INDEX IF NOT EXISTS idx_trees_status ON trees(status);
CREATE INDEX IF NOT EXISTS idx_trees_species ON trees(tree_species);

-- Vector indexes (IVFFlat for similarity search)
CREATE INDEX IF NOT EXISTS idx_global_features 
    ON tree_scans USING ivfflat (global_features vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_multiscale_features 
    ON tree_scans USING ivfflat (multiscale_features vector_cosine_ops)
    WITH (lists = 100);

-- ===== TRIGGERS =====
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trees_updated_at
    BEFORE UPDATE ON trees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ===== VIEWS =====
CREATE OR REPLACE VIEW tree_summary AS
SELECT 
    t.tree_id,
    t.tree_species,
    t.first_seen,
    t.last_seen,
    t.total_scans,
    t.status,
    ts_first.health_score as initial_health,
    ts_last.health_score as current_health,
    ts_first.area as initial_area,
    ts_last.area as current_area,
    (ts_last.area - ts_first.area) / ts_first.area * 100 as growth_percent
FROM trees t
LEFT JOIN LATERAL (
    SELECT health_score, area 
    FROM tree_scans 
    WHERE tree_id = t.tree_id 
    ORDER BY scan_time ASC 
    LIMIT 1
) ts_first ON true
LEFT JOIN LATERAL (
    SELECT health_score, area 
    FROM tree_scans 
    WHERE tree_id = t.tree_id 
    ORDER BY scan_time DESC 
    LIMIT 1
) ts_last ON true
WHERE t.status = 'active';

-- ===== SAMPLE DATA (for testing) =====
-- INSERT INTO trees (tree_species) VALUES 
--     ('Terak'),
--     ('Qarag\'ay'),
--     ('Eman');