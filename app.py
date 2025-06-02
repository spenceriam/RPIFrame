#!/usr/bin/env python3
"""
Flask web application for RPIFrame DSI Photo Frame.
Adapted from InkFrame for use with DSI touchscreen display.
Provides a web interface for managing photos and configuration.
"""
import os
import sys
import logging
import json
import glob
import subprocess
import threading
import time
from datetime import datetime
from werkzeug.utils import secure_filename

from flask import Flask, request, jsonify, render_template, send_from_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rpiframe.log')
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

# Configuration
CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
    "display": {
        "width": 800,
        "height": 480,
        "rotation": 0,
        "slideshow_interval": 60,  # seconds
        "transition_effect": "fade"
    },
    "photos": {
        "directory": "photos",
        "allowed_extensions": ["png", "jpg", "jpeg", "gif", "bmp"],
        "max_upload_size_mb": 50
    },
    "system": {
        "web_port": 5000,
        "debug_mode": False,
        "enable_touch": True
    }
}

# Load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with defaults to ensure all keys exist
            for key in DEFAULT_CONFIG:
                if key not in config:
                    config[key] = DEFAULT_CONFIG[key]
                else:
                    for subkey in DEFAULT_CONFIG[key]:
                        if subkey not in config[key]:
                            config[key][subkey] = DEFAULT_CONFIG[key][subkey]
            return config
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# Load configuration
config = load_config()

# Setup upload directory
UPLOAD_FOLDER = config['photos']['directory']
ALLOWED_EXTENSIONS = set(config['photos']['allowed_extensions'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config['photos']['max_upload_size_mb'] * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'thumbnails'), exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#
# Routes
#

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/photos', methods=['GET'])
def get_photos():
    """Get a list of all photos"""
    try:
        photos = []
        # Get all photos
        for ext in ALLOWED_EXTENSIONS:
            photos.extend(glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], f'*.{ext}')))
        
        # Get all thumbnails
        thumbnails = {}
        for ext in ['jpg', 'jpeg', 'png']:
            for thumb in glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', f'*.{ext}')):
                basename = os.path.basename(thumb)
                name = os.path.splitext(basename)[0]
                thumbnails[name] = f'/photos/thumbnails/{basename}'
        
        # Format the response
        result = []
        for photo in photos:
            basename = os.path.basename(photo)
            name = os.path.splitext(basename)[0]
            photo_url = f'/photos/{basename}'
            
            # Find matching thumbnail or use the photo itself
            thumbnail_url = thumbnails.get(name, photo_url)
            
            result.append({
                'id': name,
                'name': basename,
                'url': photo_url,
                'thumbnail': thumbnail_url,
                'date_added': datetime.fromtimestamp(os.path.getctime(photo)).isoformat()
            })
        
        # Sort by date added (newest first)
        result.sort(key=lambda x: x['date_added'], reverse=True)
        
        return jsonify({'photos': result})
    except Exception as e:
        logger.error(f"Error getting photos: {e}")
        return jsonify({'error': 'Failed to get photos'}), 500

@app.route('/api/photos', methods=['POST'])
def upload_photo():
    """Upload a new photo"""
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            # Secure the filename to prevent path traversal
            filename = secure_filename(file.filename)
            
            # Save the uploaded file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Generate thumbnail
            generate_thumbnail(file_path)
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'filename': filename
            })
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        logger.error(f"Error uploading photo: {e}")
        return jsonify({'error': 'Failed to upload photo'}), 500

@app.route('/api/photos/<photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """Delete a photo"""
    try:
        # Prevent path traversal
        photo_id = secure_filename(photo_id)
        
        # Find the photo file
        photo_paths = []
        for ext in ALLOWED_EXTENSIONS:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{photo_id}.{ext}')
            if os.path.exists(photo_path):
                photo_paths.append(photo_path)
        
        # Find the thumbnail
        thumb_paths = []
        for ext in ['jpg', 'jpeg', 'png']:
            thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', f'{photo_id}.{ext}')
            if os.path.exists(thumb_path):
                thumb_paths.append(thumb_path)
        
        if not photo_paths:
            return jsonify({'error': 'Photo not found'}), 404
        
        # Delete the files
        for path in photo_paths + thumb_paths:
            os.remove(path)
            logger.info(f"Deleted file: {path}")
        
        return jsonify({'success': True, 'message': 'Photo deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting photo: {e}")
        return jsonify({'error': 'Failed to delete photo'}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get the current configuration"""
    try:
        return jsonify({'config': config})
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({'error': 'Failed to get configuration'}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update the configuration"""
    try:
        # Get the updated configuration
        updates = request.json
        
        if not updates:
            return jsonify({'error': 'No updates provided'}), 400
        
        # Update the configuration
        global config
        for key in updates:
            if key in config:
                config[key].update(updates[key])
        
        # Save configuration
        save_config(config)
        
        return jsonify({'success': True, 'message': 'Configuration updated successfully'})
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return jsonify({'error': 'Failed to update configuration'}), 500

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get system status information"""
    try:
        # Get disk usage
        total, used, free = 0, 0, 0
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
        except:
            pass
        
        # Get CPU temperature (Raspberry Pi specific)
        cpu_temp = 'N/A'
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                cpu_temp = str(float(f.read()) / 1000) + '°C'
        except:
            pass
        
        # Check if display process is running
        display_running = False
        try:
            # Check if our display process is running
            result = subprocess.run(['pgrep', '-f', 'display_slideshow.py'], 
                                  capture_output=True, text=True)
            display_running = bool(result.stdout.strip())
        except:
            pass
        
        # Format disk space
        def format_size(size_bytes):
            if size_bytes == 0:
                return "0B"
            size_name = ("B", "KB", "MB", "GB", "TB")
            i = 0
            while size_bytes >= 1024 and i < len(size_name) - 1:
                size_bytes /= 1024
                i += 1
            return f"{size_bytes:.2f} {size_name[i]}"
        
        status = {
            'disk': {
                'total': format_size(total),
                'used': format_size(used),
                'free': format_size(free),
                'percent_used': round(used / total * 100, 1) if total > 0 else 0
            },
            'cpu_temp': cpu_temp,
            'display_running': display_running,
            'photo_count': len(glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*.*'))),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'status': status})
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': 'Failed to get system status'}), 500

@app.route('/photos/<path:filename>')
def serve_photo(filename):
    """Serve photo files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Helper functions
def generate_thumbnail(image_path, size=(200, 200)):
    """Generate a thumbnail for the web interface"""
    try:
        from PIL import Image
        
        # Open the image
        image = Image.open(image_path)
        
        # Generate thumbnail path
        filename = os.path.basename(image_path)
        name, _ = os.path.splitext(filename)
        thumb_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
        os.makedirs(thumb_dir, exist_ok=True)
        thumb_path = os.path.join(thumb_dir, f"{name}.jpg")
        
        # Create thumbnail
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save the thumbnail
        image.convert('RGB').save(thumb_path, format="JPEG", quality=85)
        logger.info(f"Thumbnail generated: {thumb_path}")
        
        return thumb_path
    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}")
        return None

# Start the application
if __name__ == '__main__':
    port = config['system'].get('web_port', 5000)
    debug = config['system'].get('debug_mode', False)
    
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)