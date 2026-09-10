#!/usr/bin/env python
"""Run the backend server with error handling"""
import sys
import traceback
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

try:
    print("=" * 60)
    print("Starting Tree Recognition System Backend")
    print("=" * 60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    from utils.config import Config
    config = Config()
    
    print(f"Port: {config.API_PORT}")
    print(f"Host: {config.API_HOST}")
    print(f"Upload Dir: {config.UPLOAD_DIR}")
    
    # Ensure directories
    Config.ensure_directories()
    print("Directories created")
    
    # Import and create app
    print("Importing endpoints...")
    from api.endpoints import create_app
    
    print("Creating app...")
    app = create_app()
    print("App created successfully!")
    
    print("=" * 60)
    print(f"Starting server on http://{config.API_HOST}:{config.API_PORT}")
    print("=" * 60)
    
    # Run with threaded mode for better handling
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.DEBUG,
        threaded=True,
        use_reloader=False
    )
    
except Exception as e:
    print(f"\nERROR: Error starting server: {e}")
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)

