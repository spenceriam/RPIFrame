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
        
        # Get absolute paths
        base_dir = Path(__file__).parent.parent
        static_folder = base_dir / 'static'
        template_folder = base_dir / 'templates'
        upload_folder = base_dir / self.config.photos.get("directory", "photos")
        
        self.app = Flask(__name__, 
                        static_folder=str(static_folder),
                        template_folder=str(template_folder))
        
        # Configure Flask app
        self.app.config['MAX_CONTENT_LENGTH'] = self.config.photos.get("max_upload_size_mb", 50) * 1024 * 1024
        self.app.config['UPLOAD_FOLDER'] = str(upload_folder)
        
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
        
        @self.app.route('/api/system/logs', methods=['GET'])
        def get_system_logs():
            """Get system logs"""
            try:
                lines = int(request.args.get('lines', 50))
                logs = self._get_system_logs(lines)
                return jsonify({'success': True, 'logs': logs})
            except Exception as e:
                logger.error(f"Error getting system logs: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/system/start', methods=['POST'])
        def start_display_service():
            """Start display service"""
            try:
                result = self._start_display_service()
                if result['success']:
                    return jsonify(result)
                else:
                    return jsonify(result), 500
            except Exception as e:
                logger.error(f"Error starting display service: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/photos/<path:filename>')
        def serve_photo(filename):
            """Serve photo files"""
            upload_folder = self.app.config['UPLOAD_FOLDER']
            
            # Security check - prevent directory traversal
            from werkzeug.security import safe_join
            safe_path = safe_join(upload_folder, filename)
            if safe_path is None:
                return jsonify({'error': 'Invalid path'}), 404
            
            # Check if file exists
            if not os.path.exists(safe_path):
                logger.warning(f"Photo not found: {filename} at {safe_path}")
                return jsonify({'error': 'Photo not found'}), 404
            
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
        
        @self.app.route('/api/slideshow/next', methods=['POST'])
        def next_photo():
            """Advance to next photo in slideshow"""
            try:
                # Create a signal file that the display manager can detect
                signal_file = Path('/tmp/rpiframe_next_photo')
                signal_file.touch()
                
                logger.info("Next photo signal sent")
                return jsonify({'success': True, 'message': 'Next photo signal sent'})
                
            except Exception as e:
                logger.error(f"Error sending next photo signal: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/slideshow/current', methods=['GET'])
        def current_photo():
            """Get currently displayed photo"""
            try:
                # Check if there's a current photo file indicator
                current_file = Path('/tmp/rpiframe_current_photo')
                if current_file.exists():
                    current_photo = current_file.read_text().strip()
                    return jsonify({'success': True, 'current_photo': current_photo})
                else:
                    return jsonify({'success': True, 'current_photo': None})
                    
            except Exception as e:
                logger.error(f"Error getting current photo: {e}")
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
            
            # Convert HEIC/HEIF to JPEG if needed
            if file_path.suffix.lower() in ['.heic', '.heif']:
                converted_name = self._convert_heic_to_jpeg(file_path)
                if converted_name:
                    return converted_name
            
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
    
    def _convert_heic_to_jpeg(self, heic_path: Path) -> str:
        """Convert HEIC/HEIF file to JPEG"""
        try:
            # Try using pillow-heif if available
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
                logger.info("Using pillow-heif for HEIC conversion")
            except ImportError:
                logger.warning("pillow-heif not available, trying fallback method")
            
            # Try to open and convert with PIL
            try:
                with Image.open(heic_path) as img:
                    # Convert to RGB
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Save as JPEG
                    jpeg_path = heic_path.with_suffix('.jpg')
                    img.save(jpeg_path, 'JPEG', quality=95, optimize=True)
                    
                    # Delete original HEIC file
                    heic_path.unlink()
                    
                    logger.info(f"Converted HEIC to JPEG: {jpeg_path.name}")
                    return jpeg_path.name
                    
            except Exception as e:
                logger.error(f"PIL cannot open HEIC: {e}")
                
                # Try using pyheif as fallback
                try:
                    import pyheif
                    import numpy as np
                    
                    heif_file = pyheif.read(str(heic_path))
                    image = Image.frombytes(
                        heif_file.mode,
                        heif_file.size,
                        heif_file.data,
                        "raw",
                        heif_file.mode,
                        heif_file.stride,
                    )
                    
                    # Save as JPEG
                    jpeg_path = heic_path.with_suffix('.jpg')
                    image.save(jpeg_path, 'JPEG', quality=95, optimize=True)
                    
                    # Delete original HEIC file
                    heic_path.unlink()
                    
                    logger.info(f"Converted HEIC to JPEG using pyheif: {jpeg_path.name}")
                    return jpeg_path.name
                    
                except ImportError:
                    logger.error("pyheif not available for HEIC conversion")
                except Exception as e:
                    logger.error(f"Error converting HEIC with pyheif: {e}")
            
            # If all methods fail, keep the original file
            logger.warning(f"Could not convert HEIC file: {heic_path.name}")
            logger.info("Install 'pillow-heif' for HEIC support: pip install pillow-heif")
            return heic_path.name
            
        except Exception as e:
            logger.error(f"Error in HEIC conversion: {e}")
            return heic_path.name
    
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
            
            # Check if display service is running
            display_running = self._is_display_service_running()
            
            # Get uptime
            uptime = self._get_uptime()
            
            # Get tech stack and version information
            tech_stack = self._get_tech_stack_info()
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'photo_count': photo_count,
                'photos_directory': str(upload_dir),
                'display_running': display_running,
                'uptime': uptime,
                # Frontend expects 'disk' but we also keep 'disk_usage' for backward compatibility
                'disk': {
                    'total': format_bytes(system_info['disk_usage']['total']),
                    'used': format_bytes(system_info['disk_usage']['used']),
                    'free': format_bytes(system_info['disk_usage']['free']),
                    'percent_used': round(
                        system_info['disk_usage']['used'] / system_info['disk_usage']['total'] * 100, 1
                    ) if system_info['disk_usage']['total'] > 0 else 0
                },
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
                    'percent_used': system_info['memory_usage'].get('percent', round(
                        system_info['memory_usage']['used'] / system_info['memory_usage']['total'] * 100, 1
                    ) if system_info['memory_usage']['total'] > 0 else 0)
                },
                'cpu_usage': {
                    'percent': system_info.get('cpu_usage', {}).get('percent', 0)
                },
                'cpu_temp': system_info['cpu_temp'],
                'platform': system_info['platform'],
                'tech_stack': tech_stack
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def _get_system_logs(self, lines: int = 50) -> List[str]:
        """Get system logs"""
        log_lines = []
        try:
            # Try to read from the log file
            log_file = self.config.system.get("log_file", "rpiframe.log")
            log_path = Path(log_file)
            
            if log_path.exists():
                with open(log_path, 'r') as f:
                    all_lines = f.readlines()
                    # Get the last N lines
                    log_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            else:
                log_lines = [f"Log file not found: {log_path}\n"]
                
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            log_lines = [f"Error reading logs: {str(e)}\n"]
        
        return log_lines
    
    def _is_display_service_running(self) -> bool:
        """Check if display service is running"""
        try:
            # Check if any pygame processes are running
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'display.py' in cmdline or 'DisplayManager' in cmdline:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except ImportError:
            # If psutil not available, assume it's running if we can't tell
            logger.warning("psutil not available, cannot check display service status")
            return False
        except Exception as e:
            logger.error(f"Error checking display service status: {e}")
            return False
    
    def _get_uptime(self) -> int:
        """Get system uptime in seconds"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return int(uptime_seconds)
        except Exception as e:
            logger.error(f"Error getting uptime: {e}")
            return 0
    
    def _start_display_service(self) -> Dict[str, Any]:
        """Start display service"""
        try:
            # Check if already running
            if self._is_display_service_running():
                return {
                    'success': False,
                    'error': 'Display service is already running'
                }
            
            # Try to start the display service
            import subprocess
            import sys
            
            # Get the current working directory
            cwd = Path(__file__).parent.parent
            
            # Start the display service as a background process
            cmd = [sys.executable, 'run.py', '--display-only']
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Give it a moment to start
            import time
            time.sleep(2)
            
            # Check if it's actually running
            if self._is_display_service_running():
                return {
                    'success': True,
                    'message': 'Display service started successfully',
                    'pid': proc.pid
                }
            else:
                return {
                    'success': False,
                    'error': 'Display service failed to start'
                }
                
        except Exception as e:
            logger.error(f"Error starting display service: {e}")
            return {
                'success': False,
                'error': f'Failed to start display service: {str(e)}'
            }
    
    def _get_tech_stack_info(self) -> Dict[str, Any]:
        """Get comprehensive tech stack information and health status"""
        try:
            import sys
            import platform
            import subprocess
            import os
            
            tech_stack = {
                'core': {},
                'system': {},
                'dependencies': {},
                'hardware': {},
                'health_checks': {},
                'recommendations': []
            }
            
            # Core System Information
            tech_stack['system'] = {
                'os': f"{platform.system()} {platform.release()}",
                'arch': platform.machine(),
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'hostname': platform.node(),
                'kernel': platform.release() if platform.system() == 'Linux' else 'N/A'
            }
            
            # RPIFrame Core
            try:
                rpiframe_version = "2.0.0-refactored"  # Current version
                # Since we can respond to this request, the main service is running
                # Display functionality is integrated into the main service
                tech_stack['core']['rpiframe'] = {
                    'version': rpiframe_version,
                    'status': 'running',
                    'architecture': 'modular',
                    'last_update': 'June 2025',
                    'components': 'web + display integrated'
                }
            except:
                tech_stack['core']['rpiframe'] = {'status': 'error', 'version': 'unknown'}
            
            # Key Dependencies
            dependencies = {
                'pygame': 'Display rendering',
                'flask': 'Web interface',
                'pillow': 'Image processing', 
                'psutil': 'System monitoring'
            }
            
            for dep, description in dependencies.items():
                try:
                    if dep == 'pygame':
                        import pygame
                        version = pygame.version.ver
                        available = True
                    elif dep == 'flask':
                        import flask
                        version = flask.__version__
                        available = True
                    elif dep == 'pillow':
                        import PIL
                        version = PIL.__version__
                        available = True
                    elif dep == 'psutil':
                        import psutil
                        version = psutil.__version__
                        available = True
                    else:
                        version = 'unknown'
                        available = False
                        
                    tech_stack['dependencies'][dep] = {
                        'version': version,
                        'available': available,
                        'description': description,
                        'status': 'ok' if available else 'missing'
                    }
                except ImportError:
                    tech_stack['dependencies'][dep] = {
                        'version': 'not_installed',
                        'available': False,
                        'description': description,
                        'status': 'missing'
                    }
                except Exception as e:
                    tech_stack['dependencies'][dep] = {
                        'version': 'error',
                        'available': False,
                        'description': description,
                        'status': f'error: {str(e)}'
                    }
            
            # Hardware Information (Raspberry Pi specific)
            try:
                # Get Pi model
                with open('/proc/device-tree/model', 'r') as f:
                    pi_model = f.read().strip().replace('\x00', '')
                tech_stack['hardware']['model'] = pi_model
                
                # DSI Display detection
                dsi_connected = os.path.exists('/sys/class/backlight/10-0045/')
                tech_stack['hardware']['dsi_display'] = {
                    'connected': dsi_connected,
                    'status': 'detected' if dsi_connected else 'not_detected',
                    'resolution': '800x480' if dsi_connected else 'unknown'
                }
                
                # GPU memory split
                try:
                    gpu_mem = subprocess.check_output(['vcgencmd', 'get_mem', 'gpu'], 
                                                    text=True).strip()
                    tech_stack['hardware']['gpu_memory'] = gpu_mem.replace('gpu=', '')
                except:
                    tech_stack['hardware']['gpu_memory'] = 'unknown'
                    
            except Exception as e:
                tech_stack['hardware']['error'] = str(e)
            
            # Health Checks
            health_checks = {}
            
            # Check if all core services are working
            service_running = True  # We're responding to this request, so main service is running
            photos_exist = self.config.photos and len(self._get_photo_list()) > 0
            
            health_checks['rpiframe_service'] = {
                'status': 'ok' if service_running else 'error',
                'description': 'Main RPIFrame service (web + display integrated)'
            }
            
            health_checks['photos'] = {
                'status': 'ok' if photos_exist else 'warning',
                'description': f'{len(self._get_photo_list())} photos available'
            }
            
            # Check configuration
            config_valid = self.config.validate() if hasattr(self.config, 'validate') else True
            health_checks['configuration'] = {
                'status': 'ok' if config_valid else 'warning',
                'description': 'System configuration'
            }
            
            tech_stack['health_checks'] = health_checks
            
            # Generate recommendations
            recommendations = []
            
            if not photos_exist:
                recommendations.append({
                    'type': 'content',
                    'priority': 'high', 
                    'message': 'No photos found - upload photos to start slideshow'
                })
            
            missing_deps = [dep for dep, info in tech_stack['dependencies'].items() 
                          if not info['available']]
            if missing_deps:
                recommendations.append({
                    'type': 'dependencies',
                    'priority': 'low',
                    'message': f'Optional dependencies missing: {", ".join(missing_deps)}'
                })
            
            # Overall system health
            all_critical_ok = (service_running and photos_exist and 
                             tech_stack['dependencies']['pygame']['available'] and
                             tech_stack['dependencies']['flask']['available'])
            
            tech_stack['overall_health'] = {
                'status': 'excellent' if all_critical_ok else
                         'good' if service_running and photos_exist else 'needs_attention',
                'score': len([h for h in health_checks.values() if h['status'] == 'ok']),
                'total_checks': len(health_checks)
            }
            
            tech_stack['recommendations'] = recommendations
            
            return tech_stack
            
        except Exception as e:
            logger.error(f"Error getting tech stack info: {e}")
            return {
                'error': str(e),
                'overall_health': {'status': 'error', 'score': 0, 'total_checks': 0}
            }
    
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