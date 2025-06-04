"""
Configuration management for RPIFrame.
Handles loading, saving, and validation of configuration settings.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
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
        "allowed_extensions": ["jpg", "jpeg", "png", "bmp", "gif", "heic", "heif"],
        "max_upload_size_mb": 50,
        "thumbnail_size": 200,
        "max_dimension": 1920
    },
    "system": {
        "web_port": 5000,
        "debug_mode": False,
        "enable_touch": True,
        "log_level": "INFO",
        "log_file": "rpiframe.log"
    },
    "web": {
        "host": "0.0.0.0",
        "port": 5000,
        "upload_folder": "photos"
    }
}

class Config:
    """Configuration manager for RPIFrame"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_with_defaults(config)
            else:
                logger.info(f"Config file not found, creating default: {self.config_file}")
                self._save_config(DEFAULT_CONFIG)
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            return DEFAULT_CONFIG.copy()
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults to ensure all keys exist"""
        merged = DEFAULT_CONFIG.copy()
        
        for section, values in config.items():
            if section in merged and isinstance(values, dict):
                merged[section].update(values)
            else:
                merged[section] = values
                
        return merged
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            if key is None:
                return self._config.get(section, default)
            return self._config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section: str, key: Optional[str] = None, value: Any = None) -> None:
        """Set configuration value"""
        try:
            if key is None:
                # Setting entire section
                self._config[section] = value
            else:
                # Setting specific key in section
                if section not in self._config:
                    self._config[section] = {}
                self._config[section][key] = value
            
            self._save_config(self._config)
        except Exception as e:
            logger.error(f"Error setting config: {e}")
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update configuration with dictionary of changes"""
        try:
            for section, values in updates.items():
                if section in self._config and isinstance(values, dict):
                    self._config[section].update(values)
                else:
                    self._config[section] = values
            
            self._save_config(self._config)
        except Exception as e:
            logger.error(f"Error updating config: {e}")
    
    @property
    def display(self) -> Dict[str, Any]:
        """Get display configuration"""
        return self._config.get("display", {})
    
    @property
    def photos(self) -> Dict[str, Any]:
        """Get photos configuration"""
        return self._config.get("photos", {})
    
    @property
    def system(self) -> Dict[str, Any]:
        """Get system configuration"""
        return self._config.get("system", {})
    
    @property
    def web(self) -> Dict[str, Any]:
        """Get web configuration"""
        return self._config.get("web", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return self._config.copy()
    
    def validate(self) -> bool:
        """Validate configuration"""
        try:
            # Check required sections
            required_sections = ["display", "photos", "system", "web"]
            for section in required_sections:
                if section not in self._config:
                    logger.error(f"Missing required config section: {section}")
                    return False
            
            # Validate display settings
            display = self.display
            if not isinstance(display.get("width"), int) or display.get("width") <= 0:
                logger.error("Invalid display width")
                return False
            
            if not isinstance(display.get("height"), int) or display.get("height") <= 0:
                logger.error("Invalid display height")
                return False
            
            # Validate photos directory
            photos_dir = self.photos.get("directory", "photos")
            if not os.path.exists(photos_dir):
                try:
                    os.makedirs(photos_dir, exist_ok=True)
                    os.makedirs(os.path.join(photos_dir, "thumbnails"), exist_ok=True)
                except Exception as e:
                    logger.error(f"Cannot create photos directory: {e}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return False