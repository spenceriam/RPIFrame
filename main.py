#!/usr/bin/env python3
"""
Main entry point for RPIFrame DSI Photo Frame.
Manages both the web server and display slideshow components.
"""
import os
import sys
import argparse
import logging
import threading
import time
import signal
from multiprocessing import Process

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

# Global process references
web_process = None
display_process = None
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False
    stop_services()
    sys.exit(0)

def start_web_server(port=5000, debug=False):
    """Start the Flask web server"""
    try:
        logger.info(f"Starting web server on port {port}")
        from app import app
        app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
    except Exception as e:
        logger.error(f"Error starting web server: {e}")

def start_display_slideshow():
    """Start the display slideshow"""
    try:
        logger.info("Starting display slideshow with pygame")
        from display_slideshow import main as display_main
        display_main()
    except Exception as e:
        logger.error(f"Error starting pygame display slideshow: {e}")
        logger.info("Falling back to simple framebuffer slideshow")
        try:
            from simple_slideshow import main as simple_main
            simple_main()
        except Exception as e2:
            logger.error(f"Error starting simple slideshow: {e2}")

def stop_services():
    """Stop all running services"""
    global web_process, display_process
    
    logger.info("Stopping services...")
    
    if web_process and web_process.is_alive():
        logger.info("Terminating web server...")
        web_process.terminate()
        web_process.join(timeout=5)
        if web_process.is_alive():
            web_process.kill()
    
    if display_process and display_process.is_alive():
        logger.info("Terminating display slideshow...")
        display_process.terminate()
        display_process.join(timeout=5)
        if display_process.is_alive():
            display_process.kill()
    
    logger.info("All services stopped")

def check_environment():
    """Check if running on Raspberry Pi with proper environment"""
    is_raspberry_pi = False
    
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' in model:
                is_raspberry_pi = True
                logger.info(f"Running on: {model.strip()}")
    except:
        pass
    
    if not is_raspberry_pi:
        logger.warning("Not running on Raspberry Pi - display features may not work properly")
    
    # Check for required directories
    required_dirs = ['photos', 'photos/thumbnails', 'static', 'templates']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
    
    return is_raspberry_pi

def main():
    """Main entry point"""
    global web_process, display_process, running
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='RPIFrame DSI Photo Frame')
    parser.add_argument('--web-only', action='store_true', help='Run only the web interface')
    parser.add_argument('--display-only', action='store_true', help='Run only the display slideshow')
    parser.add_argument('--port', type=int, default=5000, help='Web server port (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-display', action='store_true', help='Disable display output (for development)')
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check environment
    is_raspberry_pi = check_environment()
    
    # Determine what to run
    run_web = not args.display_only
    run_display = not args.web_only and not args.no_display
    
    if not is_raspberry_pi and run_display and not args.no_display:
        logger.warning("Display slideshow disabled - not running on Raspberry Pi")
        run_display = False
    
    logger.info("Starting RPIFrame...")
    logger.info(f"Web interface: {'Enabled' if run_web else 'Disabled'}")
    logger.info(f"Display slideshow: {'Enabled' if run_display else 'Disabled'}")
    
    try:
        # Start web server process
        if run_web:
            web_process = Process(target=start_web_server, args=(args.port, args.debug))
            web_process.start()
            logger.info("Web server process started")
            
            # Give web server time to start
            time.sleep(2)
        
        # Start display slideshow process
        if run_display:
            display_process = Process(target=start_display_slideshow)
            display_process.start()
            logger.info("Display slideshow process started")
        
        # Monitor processes
        while running:
            # Check if processes are still alive
            if web_process and not web_process.is_alive():
                logger.error("Web server process died unexpectedly")
                if run_display:
                    stop_services()
                    sys.exit(1)
            
            if display_process and not display_process.is_alive():
                logger.error("Display slideshow process died unexpectedly")
                # Restart display process
                logger.info("Attempting to restart display slideshow...")
                display_process = Process(target=start_display_slideshow)
                display_process.start()
            
            time.sleep(5)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        stop_services()
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        stop_services()
        sys.exit(0)

if __name__ == '__main__':
    main()