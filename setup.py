#!/usr/bin/env python3
"""
RPIFrame Setup and Installation Script
Handles dependency installation and initial configuration.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, check=True, capture_output=False):
    """Run a shell command"""
    print(f"Running: {cmd}")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if check:
            sys.exit(1)

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or newer is required")
        sys.exit(1)
    print(f"Python version: {sys.version}")

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    
    # Update pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip")
    
    # Install from requirements
    req_file = Path(__file__).parent / "requirements-new.txt"
    if req_file.exists():
        run_command(f"{sys.executable} -m pip install -r {req_file}")
    else:
        print("Warning: requirements-new.txt not found, installing basic dependencies")
        run_command(f"{sys.executable} -m pip install Flask Pillow psutil")
        
        # Try to install pygame (may fail on non-Pi systems)
        try:
            run_command(f"{sys.executable} -m pip install pygame", check=False)
        except:
            print("Warning: pygame installation failed (may be normal on non-Pi systems)")

def setup_directories():
    """Create required directories"""
    print("\nSetting up directories...")
    
    dirs = [
        "photos",
        "photos/thumbnails", 
        "static",
        "static/css",
        "static/js",
        "static/images",
        "templates",
        "logs"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"Created: {dir_path}")

def create_default_config():
    """Create default configuration file"""
    print("\nCreating default configuration...")
    
    config_file = Path("config.json")
    if config_file.exists():
        print("Configuration file already exists, skipping")
        return
    
    default_config = """{
  "display": {
    "width": 800,
    "height": 480,
    "rotation": 0,
    "slideshow_interval": 60,
    "transition_effect": "fade",
    "brightness": 100,
    "fit_mode": "contain"
  },
  "photos": {
    "directory": "photos",
    "allowed_extensions": ["jpg", "jpeg", "png", "bmp", "gif"],
    "max_upload_size_mb": 50,
    "thumbnail_size": 200,
    "max_dimension": 1920
  },
  "system": {
    "web_port": 5000,
    "debug_mode": false,
    "enable_touch": true,
    "log_level": "INFO",
    "log_file": "logs/rpiframe.log"
  },
  "web": {
    "host": "0.0.0.0",
    "port": 5000,
    "upload_folder": "photos"
  }
}"""
    
    with open(config_file, 'w') as f:
        f.write(default_config)
    
    print(f"Created: {config_file}")

def create_basic_template():
    """Create basic HTML template if not exists"""
    template_file = Path("templates/index.html")
    if template_file.exists():
        return
    
    print("Creating basic HTML template...")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPIFrame - Photo Management</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { text-align: center; margin-bottom: 30px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin-bottom: 30px; }
        .upload-area:hover { border-color: #007bff; }
        .photos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
        .photo-item { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
        .photo-item img { width: 100%; height: 150px; object-fit: cover; }
        .photo-info { padding: 10px; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .status { margin: 20px 0; padding: 15px; border-radius: 4px; }
        .status.success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .status.error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RPIFrame Photo Management</h1>
            <p>Upload and manage photos for your digital photo frame</p>
        </div>
        
        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
            <input type="file" id="fileInput" multiple accept="image/*" style="display: none;">
            <h3>Click to Upload Photos</h3>
            <p>Or drag and drop images here</p>
        </div>
        
        <div id="status"></div>
        
        <div class="photos-grid" id="photosGrid">
            <!-- Photos will be loaded here -->
        </div>
    </div>

    <script>
        // Basic JavaScript for photo management
        const fileInput = document.getElementById('fileInput');
        const photosGrid = document.getElementById('photosGrid');
        const status = document.getElementById('status');

        fileInput.addEventListener('change', handleFileUpload);

        function showStatus(message, type = 'success') {
            status.innerHTML = `<div class="status ${type}">${message}</div>`;
            setTimeout(() => status.innerHTML = '', 5000);
        }

        function handleFileUpload(event) {
            const files = event.target.files;
            for (let file of files) {
                uploadFile(file);
            }
        }

        function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            fetch('/api/photos', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus(`Uploaded: ${file.name}`, 'success');
                    loadPhotos();
                } else {
                    showStatus(`Error uploading ${file.name}: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                showStatus(`Error uploading ${file.name}: ${error}`, 'error');
            });
        }

        function loadPhotos() {
            fetch('/api/photos')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayPhotos(data.photos);
                }
            })
            .catch(error => console.error('Error loading photos:', error));
        }

        function displayPhotos(photos) {
            photosGrid.innerHTML = '';
            photos.forEach(photo => {
                const photoDiv = document.createElement('div');
                photoDiv.className = 'photo-item';
                photoDiv.innerHTML = `
                    <img src="${photo.thumbnail}" alt="${photo.name}">
                    <div class="photo-info">
                        <strong>${photo.name}</strong><br>
                        <small>${photo.size}</small><br>
                        <button class="btn btn-danger" onclick="deletePhoto('${photo.id}')">Delete</button>
                    </div>
                `;
                photosGrid.appendChild(photoDiv);
            });
        }

        function deletePhoto(photoId) {
            if (confirm('Are you sure you want to delete this photo?')) {
                fetch(`/api/photos/${photoId}`, { method: 'DELETE' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('Photo deleted successfully', 'success');
                        loadPhotos();
                    } else {
                        showStatus(`Error deleting photo: ${data.error}`, 'error');
                    }
                })
                .catch(error => {
                    showStatus(`Error deleting photo: ${error}`, 'error');
                });
            }
        }

        // Load photos on page load
        loadPhotos();
    </script>
</body>
</html>"""
    
    with open(template_file, 'w') as f:
        f.write(html_content)
    
    print(f"Created: {template_file}")

def setup_systemd_service():
    """Setup systemd service (Linux only)"""
    if platform.system() != 'Linux':
        print("Skipping systemd service setup (not on Linux)")
        return
    
    print("\nSetting up systemd service...")
    
    script_dir = Path(__file__).parent.absolute()
    service_content = f"""[Unit]
Description=RPIFrame Digital Photo Frame
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory={script_dir}
ExecStart={sys.executable} {script_dir}/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("/etc/systemd/system/rpiframe.service")
    
    try:
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        run_command("sudo systemctl daemon-reload")
        print(f"Created systemd service: {service_file}")
        print("To enable at boot: sudo systemctl enable rpiframe")
        print("To start now: sudo systemctl start rpiframe")
        
    except PermissionError:
        print("Warning: Could not create systemd service (need sudo)")
        print("You can manually create the service file later")

def main():
    """Main setup function"""
    print("RPIFrame Setup and Installation")
    print("==============================")
    
    check_python_version()
    install_dependencies()
    setup_directories()
    create_default_config()
    create_basic_template()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--systemd':
        setup_systemd_service()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Run: python3 run.py --web-only")
    print("2. Open browser to: http://localhost:5000")
    print("3. Upload some photos")
    print("4. On Raspberry Pi, run: python3 run.py")
    print("\nFor help: python3 run.py --help")

if __name__ == '__main__':
    main()