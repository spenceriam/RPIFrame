"""
Utility functions for RPIFrame.
Common helper functions for logging, directory management, etc.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config

def setup_logging(config: 'Config') -> None:
    """Setup logging configuration"""
    try:
        log_level = getattr(logging, config.system.get("log_level", "INFO").upper())
        log_file = config.system.get("log_file", "rpiframe.log")
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        if log_path.parent != Path("."):
            log_path.parent.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                )
            ]
        )
        
        # Set specific logger levels
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        logging.basicConfig(level=logging.INFO)

def create_directories(config: 'Config') -> None:
    """Create required directories"""
    try:
        # Photos directory
        photos_dir = Path(config.photos.get("directory", "photos"))
        photos_dir.mkdir(exist_ok=True)
        
        # Thumbnails directory
        thumbs_dir = photos_dir / "thumbnails"
        thumbs_dir.mkdir(exist_ok=True)
        
        # Static directories (for web interface)
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        
        (static_dir / "css").mkdir(exist_ok=True)
        (static_dir / "js").mkdir(exist_ok=True)
        (static_dir / "images").mkdir(exist_ok=True)
        
        # Templates directory
        templates_dir = Path("templates")
        templates_dir.mkdir(exist_ok=True)
        
        # Logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating directories: {e}")

def get_system_info() -> dict:
    """Get system information"""
    info = {
        "platform": "unknown",
        "cpu_temp": "N/A",
        "disk_usage": {"total": 0, "used": 0, "free": 0},
        "memory_usage": {"total": 0, "used": 0, "free": 0}
    }
    
    try:
        import platform
        info["platform"] = platform.system()
        
        # CPU temperature (Raspberry Pi specific)
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_raw = int(f.read().strip())
                info["cpu_temp"] = f"{temp_raw / 1000:.1f}°C"
        except:
            pass
        
        # Disk usage
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            info["disk_usage"] = {
                "total": total,
                "used": used,
                "free": free
            }
        except:
            pass
        
        # Memory usage
        try:
            import psutil
            memory = psutil.virtual_memory()
            info["memory_usage"] = {
                "total": memory.total,
                "used": memory.used,
                "free": memory.available
            }
        except ImportError:
            pass
        except:
            pass
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Error getting system info: {e}")
    
    return info

def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable string"""
    if bytes_value == 0:
        return "0B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    value = float(bytes_value)
    
    while value >= 1024 and i < len(units) - 1:
        value /= 1024
        i += 1
    
    return f"{value:.1f} {units[i]}"

def is_image_file(filename: str, allowed_extensions: list) -> bool:
    """Check if file is an allowed image type"""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in [ext.lower() for ext in allowed_extensions]

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing problematic characters"""
    import re
    from werkzeug.utils import secure_filename
    
    # First pass through werkzeug's secure_filename
    safe_name = secure_filename(filename)
    
    # Additional safety measures
    safe_name = re.sub(r'[^\w\-_\.]', '_', safe_name)
    safe_name = re.sub(r'_{2,}', '_', safe_name)  # Replace multiple underscores
    safe_name = safe_name.strip('_')  # Remove leading/trailing underscores
    
    # Ensure we don't have an empty filename
    if not safe_name:
        safe_name = "unnamed_file"
    
    return safe_name