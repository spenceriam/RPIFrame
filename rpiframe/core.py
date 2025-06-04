"""
Core PhotoFrame class that orchestrates the entire application.
Manages display, web server, and overall application lifecycle.
"""

import os
import sys
import signal
import logging
import threading
import time
from pathlib import Path
from multiprocessing import Process, Queue
from typing import Optional

from .config import Config
from .display import DisplayManager
from .web import WebServer
from .utils import setup_logging, create_directories

logger = logging.getLogger(__name__)

class PhotoFrame:
    """Main PhotoFrame application orchestrator"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize PhotoFrame application"""
        self.config = Config(config_file)
        self.display_process: Optional[Process] = None
        self.web_process: Optional[Process] = None
        self.running = False
        self.web_only = False
        self.display_only = False
        
        # Setup logging
        setup_logging(self.config)
        
        # Validate configuration
        if not self.config.validate():
            logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Create required directories
        create_directories(self.config)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("PhotoFrame initialized")
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _start_web_server(self, queue: Queue) -> None:
        """Start web server in separate process"""
        try:
            web_server = WebServer(self.config)
            queue.put("WEB_STARTED")
            web_server.run()
        except Exception as e:
            logger.error(f"Web server error: {e}")
            queue.put(f"WEB_ERROR:{e}")
    
    def _start_display_manager(self, queue: Queue) -> None:
        """Start display manager in separate process"""
        try:
            display_manager = DisplayManager(self.config)
            queue.put("DISPLAY_STARTED")
            display_manager.run()
        except Exception as e:
            logger.error(f"Display manager error: {e}")
            queue.put(f"DISPLAY_ERROR:{e}")
    
    def start(self, web_only: bool = False, display_only: bool = False) -> None:
        """Start the PhotoFrame application"""
        self.web_only = web_only
        self.display_only = display_only
        self.running = True
        
        logger.info("Starting PhotoFrame application")
        logger.info(f"Mode: Web Only={web_only}, Display Only={display_only}")
        
        # Check if running on Raspberry Pi
        is_pi = self._is_raspberry_pi()
        if not is_pi and not web_only:
            logger.warning("Not running on Raspberry Pi - display features may not work")
            if not display_only:
                logger.info("Switching to web-only mode")
                self.web_only = True
                self.display_only = False
        
        try:
            # Start web server
            if not display_only:
                web_queue = Queue()
                self.web_process = Process(
                    target=self._start_web_server,
                    args=(web_queue,),
                    name="WebServer"
                )
                self.web_process.start()
                
                # Wait for web server to start
                try:
                    result = web_queue.get(timeout=10)
                    if result.startswith("WEB_ERROR"):
                        raise Exception(result.split(":", 1)[1])
                    logger.info("Web server started successfully")
                except Exception as e:
                    logger.error(f"Failed to start web server: {e}")
                    self.stop()
                    return
            
            # Start display manager
            if not web_only and is_pi:
                display_queue = Queue()
                self.display_process = Process(
                    target=self._start_display_manager,
                    args=(display_queue,),
                    name="DisplayManager"
                )
                self.display_process.start()
                
                # Wait for display manager to start
                try:
                    result = display_queue.get(timeout=10)
                    if result.startswith("DISPLAY_ERROR"):
                        logger.warning(f"Display manager error: {result.split(':', 1)[1]}")
                        logger.warning("Continuing with web-only mode")
                    else:
                        logger.info("Display manager started successfully")
                except Exception as e:
                    logger.warning(f"Display manager startup timeout: {e}")
                    logger.warning("Continuing with web-only mode")
            
            # Monitor processes
            self._monitor_processes()
            
        except Exception as e:
            logger.error(f"Fatal error starting PhotoFrame: {e}")
            self.stop()
            raise
    
    def stop(self) -> None:
        """Stop all processes gracefully"""
        logger.info("Stopping PhotoFrame application")
        self.running = False
        
        # Stop web server
        if self.web_process and self.web_process.is_alive():
            logger.info("Stopping web server...")
            self.web_process.terminate()
            self.web_process.join(timeout=5)
            if self.web_process.is_alive():
                logger.warning("Force killing web server")
                self.web_process.kill()
                self.web_process.join()
        
        # Stop display manager
        if self.display_process and self.display_process.is_alive():
            logger.info("Stopping display manager...")
            self.display_process.terminate()
            self.display_process.join(timeout=5)
            if self.display_process.is_alive():
                logger.warning("Force killing display manager")
                self.display_process.kill()
                self.display_process.join()
        
        logger.info("PhotoFrame stopped")
    
    def _monitor_processes(self) -> None:
        """Monitor running processes and restart if needed"""
        logger.info("Starting process monitoring")
        
        while self.running:
            try:
                # Check web server
                if not self.display_only and self.web_process:
                    if not self.web_process.is_alive():
                        logger.error("Web server process died")
                        self.stop()
                        break
                
                # Check display manager
                if not self.web_only and self.display_process:
                    if not self.display_process.is_alive():
                        logger.warning("Display manager process died, attempting restart...")
                        # Restart display process
                        display_queue = Queue()
                        self.display_process = Process(
                            target=self._start_display_manager,
                            args=(display_queue,),
                            name="DisplayManager"
                        )
                        self.display_process.start()
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Monitoring interrupted")
                break
            except Exception as e:
                logger.error(f"Error in process monitoring: {e}")
                time.sleep(5)
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                if 'Raspberry Pi' in model:
                    logger.info(f"Running on: {model.strip()}")
                    return True
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(f"Error checking Pi model: {e}")
        
        logger.info("Not running on Raspberry Pi")
        return False
    
    def get_status(self) -> dict:
        """Get current application status"""
        return {
            "running": self.running,
            "web_server": {
                "enabled": not self.display_only,
                "running": self.web_process.is_alive() if self.web_process else False,
                "port": self.config.web.get("port", 5000)
            },
            "display_manager": {
                "enabled": not self.web_only,
                "running": self.display_process.is_alive() if self.display_process else False
            },
            "config": {
                "photos_directory": self.config.photos.get("directory", "photos"),
                "slideshow_interval": self.config.display.get("slideshow_interval", 60)
            }
        }