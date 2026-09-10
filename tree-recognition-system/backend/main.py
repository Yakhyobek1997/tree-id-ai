
import os
import sys
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
from utils.config import Config
from api.endpoints import create_app

# Load environment variables from project root
env_path = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path=env_path)
print(f"Loading .env from: {env_path}")
print(f".env exists: {env_path.exists()}")

if __name__ == "__main__":
    config = Config()
    
    print("=" * 60)
    print("🌳 TREE RECOGNITION SYSTEM")
    print("=" * 60)
    print(f" Version: {config.APP_VERSION}")
    print(f" API: http://{config.API_HOST}:{config.API_PORT}")
    print(f" Upload Dir: {config.UPLOAD_DIR}")
    print(f" Database Type: {config.DB_TYPE}")
    print(f" Diagnostics AI configured: {bool(Config.PLANTNET_API_KEY)}")
    print(f" Debug Mode: {config.DEBUG}")
    print("=" * 60)
    
    # Create directories
    Config.ensure_directories()
    
    # Create Flask app
    app = create_app()
    
    # Run server
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.DEBUG
    )
