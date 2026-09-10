"""
API Endpoints
Flask REST API for tree recognition system
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import uuid
import os
from datetime import datetime
from typing import Dict, Any
import traceback

from models import FeatureExtractor, TreeMatcher, TemporalAnalyzer
from database import DatabaseManager
from utils import Config, ImagePreprocessor
from analysis.provider import PlantNetProvider
from analysis.service import AnalysisService
from analysis.store import AnalysisStore
from .analysis_routes import create_analysis_blueprint


def _serialize_for_json(obj):
    """
    Convert numpy arrays and other non-JSON-serializable objects to JSON-serializable format
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON-serializable object
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: _serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    else:
        return obj


def create_app(db_manager: DatabaseManager = None) -> Flask:
    """
    Create and configure Flask application
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, origins=Config.CORS_ORIGINS)
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Initialize components
    if db_manager is None:
        # Get database connection string based on type
        connection_string = Config.get_db_connection_string()
        
        # For MongoDB, pass database name as well
        if Config.DB_TYPE == 'mongodb':
            db_manager = DatabaseManager(
                db_type=Config.DB_TYPE,
                connection_string=connection_string,
                database_name=Config.MONGO_DATABASE
            )
        else:
            db_manager = DatabaseManager(
                db_type=Config.DB_TYPE,
                connection_string=connection_string
            )
    
    feature_extractor = FeatureExtractor(model_path=Config.FEATURE_EXTRACTOR_MODEL)
    tree_matcher = TreeMatcher(
        similarity_threshold=Config.SIMILARITY_THRESHOLD,
        high_confidence_threshold=Config.HIGH_CONFIDENCE_THRESHOLD
    )
    temporal_analyzer = TemporalAnalyzer()
    image_preprocessor = ImagePreprocessor(target_size=Config.FEATURE_EXTRACTOR_INPUT_SIZE)
    
    # Store in app context
    app.config['db_manager'] = db_manager
    app.config['feature_extractor'] = feature_extractor
    app.config['tree_matcher'] = tree_matcher
    app.config['temporal_analyzer'] = temporal_analyzer
    app.config['image_preprocessor'] = image_preprocessor
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_UPLOAD_SIZE
    analysis_service = AnalysisService(
        PlantNetProvider(Config.PLANTNET_API_KEY, Config.PLANTNET_PROJECT, Config.PLANTNET_TIMEOUT),
        Config.ANALYSIS_MIN_SCORE, Config.ANALYSIS_MIN_MARGIN,
    )
    app.register_blueprint(create_analysis_blueprint(
        analysis_service, AnalysisStore(Config.ANALYSIS_DB_PATH),
    ))
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': db_manager.db_type
        })
    
    @app.route('/api/register-tree', methods=['POST'])
    def register_tree():
        """Register a new tree"""
        img_path = None
        try:
            if 'image' not in request.files:
                return jsonify({
                    'error': 'Image is required',
                    'message': 'Iltimos, rasm yuboring'
                }), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({
                    'error': 'No image selected',
                    'message': 'Rasm tanlanmadi'
                }), 400
            
            if not _allowed_file(file.filename):
                return jsonify({
                    'error': 'Invalid file type',
                    'message': 'Noto\'g\'ri fayl formati'
                }), 400
            
            # Save uploaded file
            filename = f"{uuid.uuid4()}_{file.filename}"
            img_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            file.save(img_path)
            
            # Validate image
            is_valid, error_msg = image_preprocessor.validate_image(img_path)
            if not is_valid:
                if os.path.exists(img_path):
                    os.remove(img_path)
                return jsonify({
                    'error': error_msg,
                    'message': 'Rasm noto\'g\'ri'
                }), 400
            
            # Preprocess image
            if Config.IMAGE_PREPROCESSING_ENABLED:
                processed_img = image_preprocessor.preprocess(img_path)
                from PIL import Image
                Image.fromarray(processed_img).save(img_path)
            
            # Extract features
            features = feature_extractor.extract_features(img_path)
            
            # Get optional parameters
            tree_type = request.form.get('tree_type', 'unknown')
            location_lat = request.form.get('location_lat')
            location_lng = request.form.get('location_lng')
            location_address = request.form.get('location_address')
            
            # Check for duplicates
            print(f"🔍 Checking for duplicates...")
            existing_trees = db_manager.get_all_trees_with_features()
            print(f"📊 Found {len(existing_trees)} trees in database")
            
            duplicate_check = tree_matcher.check_duplicate(
                features,
                existing_trees,
                duplicate_threshold=Config.DUPLICATE_THRESHOLD
            )
            
            if duplicate_check:
                print(f"⚠️  DUPLICATE FOUND: {duplicate_check['tree_id']} (similarity: {duplicate_check['similarity']:.2%})")
                if os.path.exists(img_path):
                    os.remove(img_path)
                
                # Get tree data and serialize
                tree_data = db_manager.get_tree(duplicate_check['tree_id'])
                if tree_data:
                    tree_data = _serialize_for_json(tree_data)
                
                return jsonify({
                    'status': 'exists',
                    'tree_id': duplicate_check['tree_id'],
                    'similarity': float(duplicate_check['similarity']),
                    'message': f'⚠️ Bu daraxt allaqachon bazada mavjud! (O\'xshashlik: {duplicate_check["similarity"]:.1%})',
                    'warning': 'Bu daraxt avval ro\'yxatdan o\'tgan',
                    'tree_data': tree_data
                }), 200
            
            print(f"✅ No duplicates found, registering new tree...")
            
            # Generate tree ID
            tree_id = str(uuid.uuid4())
            
            # Add to database
            success = db_manager.add_tree(
                tree_id=tree_id,
                tree_type=tree_type,
                location_lat=float(location_lat) if location_lat else None,
                location_lng=float(location_lng) if location_lng else None,
                location_address=location_address,
                features=features,
                image_path=img_path
            )
            
            if not success:
                if os.path.exists(img_path):
                    os.remove(img_path)
                return jsonify({
                    'error': 'Failed to register tree',
                    'message': 'Daraxtni ro\'yxatga olishda xatolik'
                }), 500
            
            return jsonify({
                'success': True,
                'status': 'registered',
                'tree_id': tree_id,
                'tree_type': tree_type,
                'message': 'Daraxt muvaffaqiyatli ro\'yxatga olindi!',
                'similarity': 1.0
            }), 201
            
        except Exception as e:
            if img_path and os.path.exists(img_path):
                os.remove(img_path)
            print(f"Error registering tree: {traceback.format_exc()}")
            return jsonify({
                'error': str(e),
                'message': 'Xatolik yuz berdi'
            }), 500
    
    @app.route('/api/identify-tree', methods=['POST'])
    def identify_tree():
        """Identify a tree from image"""
        img_path = None
        try:
            if 'image' not in request.files:
                return jsonify({
                    'error': 'Image is required',
                    'message': 'Iltimos, rasm yuboring'
                }), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({
                    'error': 'No image selected',
                    'message': 'Rasm tanlanmadi'
                }), 400
            
            if not _allowed_file(file.filename):
                return jsonify({
                    'error': 'Invalid file type',
                    'message': 'Noto\'g\'ri fayl formati'
                }), 400
            
            # Save uploaded file
            filename = f"{uuid.uuid4()}_{file.filename}"
            img_path = os.path.join(Config.UPLOAD_FOLDER, filename)
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            file.save(img_path)
            
            # Validate and preprocess
            is_valid, error_msg = image_preprocessor.validate_image(img_path)
            if not is_valid:
                if os.path.exists(img_path):
                    os.remove(img_path)
                return jsonify({
                    'error': error_msg,
                    'message': 'Rasm noto\'g\'ri'
                }), 400
            
            if Config.IMAGE_PREPROCESSING_ENABLED:
                processed_img = image_preprocessor.preprocess(img_path)
                from PIL import Image
                Image.fromarray(processed_img).save(img_path)
            
            # Extract features
            print(f"🔍 Extracting features from: {img_path}")
            features = feature_extractor.extract_features(img_path)
            print(f"📊 Feature vector shape: {features.shape}")
            print(f"📊 Feature vector stats: min={features.min():.3f}, max={features.max():.3f}, mean={features.mean():.3f}, std={features.std():.3f}")
            
            # Get all trees with features
            database_trees = db_manager.get_all_trees_with_features()
            print(f"🌳 Found {len(database_trees)} trees in database with features")
            
            # Find best match
            print(f"🔎 Finding best match...")
            best_match = tree_matcher.find_best_match(features, database_trees)
            
            if best_match:
                print(f"✅ Match found: {best_match['tree_id'][:8]}... (similarity: {best_match['similarity']:.2%})")
            else:
                print(f"❌ No match found above threshold")
            
            # Clean up temp file
            if os.path.exists(img_path):
                os.remove(img_path)
            
            if best_match:
                # Serialize tree data (remove features to avoid sending large arrays)
                tree_data = best_match.get('tree_data', {}).copy() if best_match.get('tree_data') else {}
                tree_data.pop('features', None)  # Remove features array from response
                
                return jsonify({
                    'success': True,
                    'found': True,
                    'tree_id': best_match['tree_id'],
                    'tree_type': tree_data.get('tree_type'),
                    'confidence': best_match.get('confidence', 'medium'),
                    'similarity': float(best_match.get('similarity', 0.0)),
                    'message': 'Daraxt topildi!',
                    'tree_data': _serialize_for_json(tree_data)
                }), 200
            else:
                return jsonify({
                    'success': True,
                    'found': False,
                    'message': 'Bu daraxt bazada yo\'q',
                    'similarity': 0.0,
                    'confidence': 0.0
                }), 200
            
        except Exception as e:
            if img_path and os.path.exists(img_path):
                os.remove(img_path)
            print(f"Error identifying tree: {traceback.format_exc()}")
            return jsonify({
                'error': str(e),
                'message': 'Xatolik yuz berdi'
            }), 500
    
    @app.route('/api/trees', methods=['GET'])
    def get_trees():
        """Get list of all trees"""
        try:
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            trees = db_manager.get_all_trees(limit=limit, offset=offset)
            
            # Serialize for JSON
            trees = _serialize_for_json(trees)
            
            return jsonify({
                'trees': trees,
                'count': len(trees),
                'limit': limit,
                'offset': offset
            }), 200
            
        except Exception as e:
            print(f"Error getting trees: {traceback.format_exc()}")
            return jsonify({
                'error': str(e),
                'message': 'Xatolik yuz berdi'
            }), 500
    
    @app.route('/api/trees/<tree_id>', methods=['GET'])
    def get_tree(tree_id: str):
        """Get specific tree by ID"""
        try:
            tree = db_manager.get_tree(tree_id)
            
            if tree:
                # Get features
                features = db_manager.get_tree_features(tree_id)
                tree['has_features'] = features is not None
                
                # Get observations if requested
                if request.args.get('include_observations') == 'true':
                    observations = db_manager.get_observations(tree_id)
                    tree['observations'] = _serialize_for_json(observations)
                
                # Serialize for JSON
                tree = _serialize_for_json(tree)
                
                return jsonify(tree), 200
            else:
                return jsonify({
                    'error': 'Tree not found',
                    'message': 'Daraxt topilmadi'
                }), 404
                
        except Exception as e:
            print(f"Error getting tree: {traceback.format_exc()}")
            return jsonify({
                'error': str(e),
                'message': 'Xatolik yuz berdi'
            }), 500
    
    @app.route('/api/trees/<tree_id>/observations', methods=['POST'])
    def add_observation(tree_id: str):
        """Add temporal observation for a tree"""
        img_path = None
        try:
            # Check if tree exists
            tree = db_manager.get_tree(tree_id)
            if not tree:
                return jsonify({
                    'error': 'Tree not found',
                    'message': 'Daraxt topilmadi'
                }), 404
            
            # Handle image if provided
            if 'image' in request.files:
                file = request.files['image']
                if file.filename:
                    filename = f"{uuid.uuid4()}_{file.filename}"
                    img_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
                    file.save(img_path)
                    
                    # Extract features
                    features = feature_extractor.extract_features(img_path)
                else:
                    features = None
            else:
                features = None
            
            # Get optional parameters
            health_status = request.form.get('health_status')
            growth_stage = request.form.get('growth_stage')
            notes = request.form.get('notes')
            
            if features is not None:
                success = db_manager.add_observation(
                    tree_id=tree_id,
                    features=features,
                    image_path=img_path,
                    health_status=health_status,
                    growth_stage=growth_stage,
                    notes=notes
                )
                
                if success:
                    # Perform temporal analysis
                    observations = db_manager.get_observations(tree_id, limit=100)
                    if len(observations) >= 2 and Config.TEMPORAL_ANALYSIS_ENABLED:
                        analysis = temporal_analyzer.analyze_temporal_changes(observations)
                        return jsonify({
                            'status': 'success',
                            'message': 'Kuzatuv qo\'shildi',
                            'analysis': analysis
                        }), 201
                    else:
                        return jsonify({
                            'status': 'success',
                            'message': 'Kuzatuv qo\'shildi'
                        }), 201
                else:
                    return jsonify({
                        'error': 'Failed to add observation',
                        'message': 'Kuzatuvni qo\'shishda xatolik'
                    }), 500
            else:
                return jsonify({
                    'error': 'Image or features required',
                    'message': 'Rasm yoki xususiyatlar kerak'
                }), 400
                
        except Exception as e:
            if img_path and os.path.exists(img_path):
                os.remove(img_path)
            print(f"Error adding observation: {traceback.format_exc()}")
            return jsonify({
                'error': str(e),
                'message': 'Xatolik yuz berdi'
            }), 500
    
    @app.route('/api/trees/<tree_id>/observations', methods=['GET'])
    def get_observations(tree_id: str):
        """Get temporal observations for a tree"""
        try:
            limit = int(request.args.get('limit', 100))
            observations = db_manager.get_observations(tree_id, limit=limit)
            
            return jsonify({
                'tree_id': tree_id,
                'observations': observations,
                'count': len(observations)
            }), 200
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'message': 'Xatolik yuz berdi'
            }), 500
    
    @app.route('/api/trees/<tree_id>', methods=['DELETE'])
    def delete_tree(tree_id: str):
        """Delete a tree"""
        try:
            success = db_manager.delete_tree(tree_id)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Daraxt o\'chirildi'
                }), 200
            else:
                return jsonify({
                    'error': 'Failed to delete tree',
                    'message': 'Daraxtni o\'chirishda xatolik'
                }), 500
                
        except Exception as e:
            return jsonify({
                'error': str(e),
                'message': 'Xatolik yuz berdi'
            }), 500
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get system statistics"""
        try:
            # Get all trees
            trees = db_manager.get_all_trees(limit=10000)
            
            # Calculate statistics
            total_trees = len(trees)
            trees_by_type = {}
            
            for tree in trees:
                tree_type = tree.get('tree_type') or 'Unknown'
                trees_by_type[tree_type] = trees_by_type.get(tree_type, 0) + 1
            
            # Convert to list for charts
            species_breakdown = [
                {'species': species, 'count': count, 'name': species}
                for species, count in sorted(trees_by_type.items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Calculate averages (placeholder for now)
            total_scans = total_trees  # Each tree has at least 1 scan (registration)
            average_scans_per_tree = 1.0 if total_trees > 0 else 0
            
            stats = {
                'total_trees': total_trees,
                'total_scans': total_scans,
                'average_scans_per_tree': round(average_scans_per_tree, 1),
                'trees_by_type': trees_by_type,
                'species_breakdown': species_breakdown,
                'recent_activity': {
                    'today': 0,
                    'this_week': 0,
                    'this_month': total_trees
                },
                'database_type': db_manager.db_type
            }
            
            return jsonify(stats), 200
            
        except Exception as e:
            print(f"Error getting stats: {traceback.format_exc()}")
            return jsonify({
                'error': str(e),
                'message': 'Statistikani olishda xatolik'
            }), 500
    
    def _allowed_file(filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    return app
