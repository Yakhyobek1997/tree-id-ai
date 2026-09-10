# backend/utils/config.py (UPDATED)

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / '.env')

class Config:
    """Global configuration"""
    
    # Application
    APP_NAME = os.getenv('APP_NAME', 'TreeRecognitionSystem')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    MODEL_DIR = DATA_DIR / "models"
    UPLOAD_DIR = DATA_DIR / "uploads"
    
    # Database Configuration
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
    
    # SQLite
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', str(DATA_DIR / 'database' / 'trees.db'))
    
    # PostgreSQL
    POSTGRES_CONFIG = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DATABASE', 'tree_recognition'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password'),
        'port': int(os.getenv('POSTGRES_PORT', 5432))
    }
    POSTGRES_CONNECTION_STRING = os.getenv('POSTGRES_CONNECTION_STRING')
    
    # MongoDB
    MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'tree_recognition')
    MONGO_USERNAME = os.getenv('MONGO_USERNAME', '')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', '')
    MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
    
    # Legacy DB_CONFIG for backward compatibility
    DB_CONFIG = POSTGRES_CONFIG
    
    # API
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', 8000))
    API_RELOAD = os.getenv('API_RELOAD', 'True').lower() == 'true'
    
    # Model paths
    SAM_CHECKPOINT = Path(os.getenv('SAM_CHECKPOINT', MODEL_DIR / "sam_vit_h_4b8939.pth"))
    YOLO_CHECKPOINT = Path(os.getenv('YOLO_CHECKPOINT', MODEL_DIR / "yolov8x.pt"))
    
    # Thresholds
    SAME_TREE_THRESHOLD = float(os.getenv('SAME_TREE_THRESHOLD', 0.75))
    SIMILAR_SPECIES_THRESHOLD = float(os.getenv('SIMILAR_SPECIES_THRESHOLD', 0.60))
    
    # Feature weights
    FEATURE_WEIGHTS = {
        'global': float(os.getenv('WEIGHT_GLOBAL', 0.25)),
        'multiscale': float(os.getenv('WEIGHT_MULTISCALE', 0.20)),
        'local': float(os.getenv('WEIGHT_LOCAL', 0.15)),
        'color': float(os.getenv('WEIGHT_COLOR', 0.15)),
        'texture': float(os.getenv('WEIGHT_TEXTURE', 0.10)),
        'geometry': float(os.getenv('WEIGHT_GEOMETRY', 0.10)),
        'segmentation': float(os.getenv('WEIGHT_SEGMENTATION', 0.05))
    }
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # GPU
    USE_GPU = os.getenv('USE_GPU', 'True').lower() == 'true'

    # Multi-view diagnostics. Keep credentials on the backend only.
    PLANTNET_API_KEY = os.getenv('PLANTNET_API_KEY', '')
    PLANTNET_PROJECT = os.getenv('PLANTNET_PROJECT', 'all')
    PLANTNET_TIMEOUT = float(os.getenv('PLANTNET_TIMEOUT', '30'))
    ANALYSIS_MIN_SCORE = float(os.getenv('ANALYSIS_MIN_SCORE', '0.80'))
    ANALYSIS_MIN_MARGIN = float(os.getenv('ANALYSIS_MIN_MARGIN', '0.15'))
    ANALYSIS_DB_PATH = os.getenv('ANALYSIS_DB_PATH', str(DATA_DIR / 'database' / 'analyses.sqlite3'))
    
    @classmethod
    def get_db_connection_string(cls):
        """Get database connection string based on DB_TYPE"""
        if cls.DB_TYPE == 'sqlite':
            return cls.SQLITE_DB_PATH
        elif cls.DB_TYPE == 'postgresql':
            if cls.POSTGRES_CONNECTION_STRING:
                return cls.POSTGRES_CONNECTION_STRING
            return f"postgresql://{cls.POSTGRES_CONFIG['user']}:{cls.POSTGRES_CONFIG['password']}@{cls.POSTGRES_CONFIG['host']}:{cls.POSTGRES_CONFIG['port']}/{cls.POSTGRES_CONFIG['database']}"
        elif cls.DB_TYPE == 'mongodb':
            if cls.MONGO_CONNECTION_STRING:
                return cls.MONGO_CONNECTION_STRING
            if cls.MONGO_USERNAME and cls.MONGO_PASSWORD:
                return f"mongodb://{cls.MONGO_USERNAME}:{cls.MONGO_PASSWORD}@{cls.MONGO_HOST}:{cls.MONGO_PORT}/"
            return f"mongodb://{cls.MONGO_HOST}:{cls.MONGO_PORT}/"
        return str(cls.DATA_DIR / 'database' / 'trees.db')
    
    # Model paths
    FEATURE_EXTRACTOR_MODEL = os.getenv('FEATURE_EXTRACTOR_MODEL', str(MODEL_DIR / 'feature_extractor.h5'))
    FEATURE_EXTRACTOR_INPUT_SIZE = (224, 224)
    
    # Thresholds
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.75))
    HIGH_CONFIDENCE_THRESHOLD = float(os.getenv('HIGH_CONFIDENCE_THRESHOLD', 0.85))
    DUPLICATE_THRESHOLD = float(os.getenv('DUPLICATE_THRESHOLD', 0.80))  # Lowered for better duplicate detection
    
    # Upload settings
    UPLOAD_FOLDER = str(UPLOAD_DIR)
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', 52 * 1024 * 1024))  # five 10 MB views + multipart overhead
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Feature flags
    IMAGE_PREPROCESSING_ENABLED = os.getenv('IMAGE_PREPROCESSING_ENABLED', 'True').lower() == 'true'
    TEMPORAL_ANALYSIS_ENABLED = os.getenv('TEMPORAL_ANALYSIS_ENABLED', 'True').lower() == 'true'
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        (cls.DATA_DIR / 'database').mkdir(parents=True, exist_ok=True)
