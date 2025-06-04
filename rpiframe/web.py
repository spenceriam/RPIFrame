"""
Web server for RPIFrame photo management interface.
Provides REST API and web interface for uploading and managing photos.
"""

import os
import glob
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, TYPE_CHECKING

try:
    from flask import Flask, request, jsonify, render_template, send_from_directory
    from werkzeug.utils import secure_filename
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    logging.getLogger(__name__).warning("Flask not available")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.getLogger(__name__).warning("PIL not available")

if TYPE_CHECKING:
    from .config import Config

from .utils import format_bytes, get_system_info, is_image_file, safe_filename

logger = logging.getLogger(__name__)

class WebServer:
    """Flask web server for photo management"""
    
    def __init__(self, config: 'Config'):
        """Initialize web server"""
        if not FLASK_AVAILABLE:
            raise ImportError("Flask not available")
        
        self.config = config
        self.app = Flask(__name__, 
                        static_folder='../static',
                        template_folder='../templates')
        
        # Configure Flask app
        self.app.config['MAX_CONTENT_LENGTH'] = self.config.photos.get("max_upload_size_mb", 50) * 1024 * 1024
        self.app.config['UPLOAD_FOLDER'] = self.config.photos.get("directory", "photos")
        
        # Setup routes
        self._setup_routes()
        
        logger.info("WebServer initialized")
    
    def _setup_routes(self) -> None:
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page"""
            return render_template('index.html')
        
        @self.app.route('/api/photos', methods=['GET'])
        def get_photos():
            """Get list of all photos"""
            try:
                photos = self._get_photo_list()
                return jsonify({'success': True, 'photos': photos})
            except Exception as e:
                logger.error(f"Error getting photos: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/photos', methods=['POST'])
        def upload_photo():
            """Upload new photo"""
            try:
                if 'file' not in request.files:
                    return jsonify({'success': False, 'error': 'No file provided'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'success': False, 'error': 'No file selected'}), 400
                
                if not self._is_allowed_file(file.filename):
                    return jsonify({'success': False, 'error': 'File type not allowed'}), 400
                
                # Save file
                filename = self._save_uploaded_file(file)
                if filename:
                    # Generate thumbnail
                    self._generate_thumbnail(filename)
                    return jsonify({
                        'success': True, 
                        'message': 'Photo uploaded successfully',
                        'filename': filename
                    })
                else:
                    return jsonify({'success': False, 'error': 'Failed to save file'}), 500
                    
            except Exception as e:
                logger.error(f"Error uploading photo: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/photos/<photo_id>', methods=['DELETE'])
        def delete_photo(photo_id):
            """Delete photo"""
            try:
                photo_id = secure_filename(photo_id)
                
                if self._delete_photo_files(photo_id):
                    return jsonify({'success': True, 'message': 'Photo deleted successfully'})
                else:
                    return jsonify({'success': False, 'error': 'Photo not found'}), 404
                    
            except Exception as e:
                logger.error(f"Error deleting photo: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Get current configuration"""
            try:
                return jsonify({'success': True, 'config': self.config.to_dict()})
            except Exception as e:
                logger.error(f"Error getting config: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Update configuration"""
            try:
                updates = request.get_json()
                if not updates:
                    return jsonify({'success': False, 'error': 'No updates provided'}), 400
                
                self.config.update(updates)
                return jsonify({'success': True, 'message': 'Configuration updated'})
                
            except Exception as e:
                logger.error(f"Error updating config: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/system/status', methods=['GET'])
        def get_system_status():
            """Get system status"""
            try:
                status = self._get_system_status()
                return jsonify({'success': True, 'status': status})
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/photos/<path:filename>')
        def serve_photo(filename):
            """Serve photo files"""
            upload_folder = self.app.config['UPLOAD_FOLDER']
            return send_from_directory(upload_folder, filename)
        
        @self.app.route('/api/photos/<photo_id>/rotate', methods=['POST'])
        def rotate_photo(photo_id):
            """Rotate photo"""
            try:
                data = request.get_json()
                degrees = data.get('degrees', 90)
                
                if self._rotate_photo(photo_id, degrees):
                    return jsonify({'success': True, 'message': 'Photo rotated successfully'})
                else:
                    return jsonify({'success': False, 'error': 'Failed to rotate photo'}), 500
                    
            except Exception as e:
                logger.error(f"Error rotating photo: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
    
    def _get_photo_list(self) -> List[Dict[str, Any]]:
        """Get list of photos with metadata"""
        photos = []
        upload_dir = Path(self.config.photos.get("directory", "photos"))
        allowed_extensions = self.config.photos.get("allowed_extensions", [])
        
        if not upload_dir.exists():
            return photos
        
        # Find all image files
        for ext in allowed_extensions:
            for photo_path in upload_dir.glob(f"*.{ext}"):
                photos.extend(self._process_photo_file(photo_path))
            for photo_path in upload_dir.glob(f"*.{ext.upper()}"):
                photos.extend(self._process_photo_file(photo_path))
        
        # Sort by date added (newest first)
        photos.sort(key=lambda x: x.get('date_added', ''), reverse=True)
        
        return photos
    
    def _process_photo_file(self, photo_path: Path) -> List[Dict[str, Any]]:
        """Process a single photo file and return metadata"""
        try:
            stat = photo_path.stat()
            
            # Check for thumbnail
            thumb_dir = photo_path.parent / "thumbnails"
            thumb_path = thumb_dir / f"{photo_path.stem}.jpg"
            
            photo_info = {
                'id': photo_path.stem,
                'name': photo_path.name,
                'url': f'/photos/{photo_path.name}',
                'thumbnail': f'/photos/thumbnails/{thumb_path.name}' if thumb_path.exists() else f'/photos/{photo_path.name}',
                'size': format_bytes(stat.st_size),
                'date_added': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'date_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            return [photo_info]
            
        except Exception as e:
            logger.error(f"Error processing photo {photo_path}: {e}")
            return []
    
    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file type is allowed"""
        allowed_extensions = self.config.photos.get("allowed_extensions", [])
        return is_image_file(filename, allowed_extensions)
    
    def _save_uploaded_file(self, file) -> str:
        """Save uploaded file to photos directory"""
        try:
            filename = safe_filename(file.filename)
            upload_dir = Path(self.config.photos.get("directory", "photos"))
            upload_dir.mkdir(exist_ok=True)
            
            file_path = upload_dir / filename
            
            # Handle duplicate names
            counter = 1
            original_stem = file_path.stem
            while file_path.exists():
                file_path = upload_dir / f"{original_stem}_{counter}{file_path.suffix}"
                counter += 1
            
            file.save(str(file_path))
            logger.info(f"Saved uploaded file: {file_path.name}")
            
            return file_path.name
            
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            return ""
    
    def _generate_thumbnail(self, filename: str) -> bool:
        """Generate thumbnail for uploaded photo"""
        if not PIL_AVAILABLE:
            return False
        
        try:
            upload_dir = Path(self.config.photos.get("directory", "photos"))
            thumb_dir = upload_dir / "thumbnails"
            thumb_dir.mkdir(exist_ok=True)
            
            photo_path = upload_dir / filename
            thumb_size = self.config.photos.get("thumbnail_size", 200)
            
            # Generate thumbnail
            with Image.open(photo_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumb_path = thumb_dir / f"{Path(filename).stem}.jpg"
                img.save(thumb_path, 'JPEG', quality=85, optimize=True)
            
            logger.info(f"Generated thumbnail: {thumb_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating thumbnail for {filename}: {e}")
            return False
    
    def _delete_photo_files(self, photo_id: str) -> bool:
        """Delete photo and thumbnail files"""
        try:
            upload_dir = Path(self.config.photos.get("directory", "photos"))
            thumb_dir = upload_dir / "thumbnails"
            
            deleted = False
            
            # Find and delete main photo
            for ext in self.config.photos.get("allowed_extensions", []):
                photo_path = upload_dir / f"{photo_id}.{ext}"
                if photo_path.exists():
                    photo_path.unlink()
                    deleted = True
                    logger.info(f"Deleted photo: {photo_path.name}")
                
                # Also check uppercase
                photo_path = upload_dir / f"{photo_id}.{ext.upper()}"
                if photo_path.exists():
                    photo_path.unlink()
                    deleted = True
                    logger.info(f"Deleted photo: {photo_path.name}")
            
            # Delete thumbnail
            thumb_path = thumb_dir / f"{photo_id}.jpg"
            if thumb_path.exists():
                thumb_path.unlink()
                logger.info(f"Deleted thumbnail: {thumb_path.name}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting photo {photo_id}: {e}")
            return False
    
    def _rotate_photo(self, photo_id: str, degrees: int) -> bool:
        """Rotate photo by specified degrees"""
        if not PIL_AVAILABLE:
            return False
        
        try:
            upload_dir = Path(self.config.photos.get("directory", "photos"))
            
            # Find photo file
            photo_path = None
            for ext in self.config.photos.get("allowed_extensions", []):
                potential_path = upload_dir / f"{photo_id}.{ext}"
                if potential_path.exists():
                    photo_path = potential_path
                    break
                
                potential_path = upload_dir / f"{photo_id}.{ext.upper()}"
                if potential_path.exists():
                    photo_path = potential_path
                    break
            
            if not photo_path:
                return False
            
            # Rotate image
            with Image.open(photo_path) as img:
                rotated = img.rotate(-degrees, expand=True)
                rotated.save(photo_path)
            
            # Regenerate thumbnail
            self._generate_thumbnail(photo_path.name)
            
            logger.info(f"Rotated photo {photo_id} by {degrees} degrees")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating photo {photo_id}: {e}")
            return False
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            system_info = get_system_info()
            upload_dir = Path(self.config.photos.get("directory", "photos"))
            
            # Count photos
            photo_count = 0
            if upload_dir.exists():
                for ext in self.config.photos.get("allowed_extensions", []):
                    photo_count += len(list(upload_dir.glob(f"*.{ext}")))
                    photo_count += len(list(upload_dir.glob(f"*.{ext.upper()}")))
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'photo_count': photo_count,
                'photos_directory': str(upload_dir),
                'disk_usage': {
                    'total': format_bytes(system_info['disk_usage']['total']),
                    'used': format_bytes(system_info['disk_usage']['used']),
                    'free': format_bytes(system_info['disk_usage']['free']),
                    'percent_used': round(
                        system_info['disk_usage']['used'] / system_info['disk_usage']['total'] * 100, 1
                    ) if system_info['disk_usage']['total'] > 0 else 0
                },
                'memory_usage': {
                    'total': format_bytes(system_info['memory_usage']['total']),
                    'used': format_bytes(system_info['memory_usage']['used']),
                    'free': format_bytes(system_info['memory_usage']['free']),
                    'percent_used': round(
                        system_info['memory_usage']['used'] / system_info['memory_usage']['total'] * 100, 1
                    ) if system_info['memory_usage']['total'] > 0 else 0
                },
                'cpu_temp': system_info['cpu_temp'],
                'platform': system_info['platform']
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def run(self) -> None:
        """Run the web server"""
        host = self.config.web.get("host", "0.0.0.0")
        port = self.config.web.get("port", 5000)
        debug = self.config.system.get("debug_mode", False)
        
        logger.info(f"Starting web server on {host}:{port}")
        
        try:
            self.app.run(
                host=host,
                port=port,
                debug=debug,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Web server error: {e}")
            raise