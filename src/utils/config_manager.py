#!/usr/bin/env python3
"""
Configuration management for RPIFrame.
Handles loading and saving configuration with validation.
"""
import os
import json
import logging
from typing import Dict, Any
from copy import deepcopy

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration manager
        
        Args:
            config_path: Path to configuration file. If None, uses default locations.
        """
        self.config_path = config_path or self._find_config_path()
        self.config = self.load_config()
        
    def _find_config_path(self) -> str:
        """Find the configuration file path"""
        # Look for config in these locations (in order)
        search_paths = [
            'config/config.json',  # User config
            'config/default_config.json',  # Default config
            os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'default_config.json'),
        ]
        
        # Find first existing config file
        for path in search_paths:
            if os.path.exists(path):
                logger.info(f"Using configuration file: {path}")
                return path
        
        # If no config found, use default location
        default_path = 'config/config.json'
        logger.warning(f"No configuration file found. Will create at: {default_path}")
        return default_path
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            # Load default config first
            default_config = self._load_default_config()
            
            # If user config exists, load and merge
            if os.path.exists(self.config_path) and 'default' not in self.config_path:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    # Deep merge user config over defaults
                    config = self._deep_merge(default_config, user_config)
                    logger.info("Loaded user configuration")
            else:
                config = default_config
                logger.info("Using default configuration")
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Return default config on error
            return self._load_default_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        default_paths = [
            'config/default_config.json',
            os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'default_config.json'),
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error loading default config from {path}: {e}")
        
        # Return minimal config if default not found
        logger.warning("Default config not found, using minimal configuration")
        return {
            "display": {
                "resolution": {"width": 800, "height": 480},
                "rotation_interval_minutes": 5
            },
            "photos": {
                "directory": "static/images/photos"
            },
            "system": {
                "web_port": 5000
            }
        }
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save configuration
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values
        
        Args:
            updates: Dictionary of updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Deep merge updates into current config
            self.config = self._deep_merge(self.config, updates)
            
            # Save the updated configuration
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key
        
        Args:
            key: Configuration key (e.g., 'display.resolution.width')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            value = self.config
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value by dot-notation key
        
        Args:
            key: Configuration key (e.g., 'display.resolution.width')
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            parts = key.split('.')
            target = self.config
            
            # Navigate to the parent of the target key
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            
            # Set the value
            target[parts[-1]] = value
            
            # Save configuration
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Error setting configuration value: {e}")
            return False
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries
        
        Args:
            base: Base dictionary
            updates: Updates to apply
            
        Returns:
            Merged dictionary
        """
        result = deepcopy(base)
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        
        return result
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self.config = self.load_config()
        logger.info("Configuration reloaded")