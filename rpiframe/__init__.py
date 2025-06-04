"""
RPIFrame - Digital Photo Frame for Raspberry Pi DSI Display
A clean, modern photo frame application with web interface and touch controls.
"""

__version__ = "2.0.0"
__author__ = "RPIFrame Project"

from .core import PhotoFrame
from .config import Config
from .display import DisplayManager
from .web import WebServer

__all__ = ['PhotoFrame', 'Config', 'DisplayManager', 'WebServer']