#!/usr/bin/env python3
"""
Simple framebuffer slideshow for Raspberry Pi DSI display
Uses fbi (framebuffer imageviewer) which works reliably on Pi
"""
import os
import sys
import json
import glob
import time
import subprocess
import signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleSlideshow:
    def __init__(self, config_file='config.json'):
        """Initialize simple slideshow using fbi"""
        self.config = self.load_config(config_file)
        self.photos = []
        self.fbi_process = None
        self.running = False
        
        # Install fbi if not present
        self.ensure_fbi_installed()
        
    def load_config(self, config_file):
        """Load configuration from file"""
        default_config = {
            'display': {
                'slideshow_interval': 60
            },
            'photos': {
                'directory': 'photos',
                'allowed_extensions': ['jpg', 'jpeg', 'png', 'gif', 'bmp']
            }
        }
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key in loaded_config:
                        default_config[key].update(loaded_config[key])
                    else:
                        loaded_config[key] = default_config[key]
                return loaded_config
        return default_config
    
    def ensure_fbi_installed(self):
        """Ensure fbi is installed"""
        try:
            subprocess.run(['which', 'fbi'], check=True, capture_output=True)
            logger.info("fbi is installed")
        except subprocess.CalledProcessError:
            logger.info("Installing fbi...")
            subprocess.run(['sudo', 'apt', 'install', '-y', 'fbi'], check=True)
            logger.info("fbi installed successfully")
    
    def scan_photos(self):
        """Scan photos directory for images"""
        self.photos = []
        
        # Get absolute path to photos directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        photo_dir = os.path.join(script_dir, self.config['photos']['directory'])
        
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir)
            logger.warning(f"Created photos directory: {photo_dir}")
            return
        
        logger.info(f"Scanning photos in: {photo_dir}")
        
        for ext in self.config['photos']['allowed_extensions']:
            pattern = os.path.join(photo_dir, f'*.{ext}')
            found = glob.glob(pattern)
            if found:
                logger.info(f"Found {len(found)} .{ext} files")
            self.photos.extend(found)
            pattern = os.path.join(photo_dir, f'*.{ext.upper()}')
            found = glob.glob(pattern)
            if found:
                logger.info(f"Found {len(found)} .{ext.upper()} files")
            self.photos.extend(found)
        
        # Convert all paths to absolute paths
        self.photos = [os.path.abspath(p) for p in self.photos]
        self.photos.sort()
        logger.info(f"Found {len(self.photos)} total photos")
    
    def run(self):
        """Run the slideshow"""
        self.running = True
        self.scan_photos()
        
        if not self.photos:
            logger.error("No photos found in photos directory")
            # Create a test image
            self.create_test_image()
            self.scan_photos()
        
        # Kill any existing fbi processes
        subprocess.run(['sudo', 'pkill', 'fbi'], capture_output=True)
        time.sleep(1)
        
        # Build fbi command
        interval = self.config['display']['slideshow_interval']
        cmd = [
            'sudo', 'fbi',
            '-T', '1',  # Use tty1
            '-d', '/dev/fb0',  # Framebuffer device
            '-noverbose',
            '-a',  # Autozoom
            '-t', str(interval),  # Time between images
            '-blend', '500',  # Blend time in ms
            '-1',  # Loop forever (don't exit after last image)
            '--'  # End of options
        ] + self.photos
        
        logger.info(f"Starting slideshow with {len(self.photos)} photos")
        logger.info(f"Slideshow interval: {interval} seconds")
        
        # Log the command for debugging
        logger.info(f"Running command: {' '.join(cmd[:10])}... [{len(self.photos)} photos]")
        
        try:
            # Start fbi with error output
            self.fbi_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            logger.info("Slideshow process started")
            
            # Monitor the process
            while self.running:
                # Check if process is still running
                poll_result = self.fbi_process.poll()
                if poll_result is not None:
                    # Process has terminated
                    stdout, stderr = self.fbi_process.communicate()
                    logger.error(f"fbi process exited with code {poll_result}")
                    if stderr:
                        logger.error(f"fbi stderr: {stderr.decode('utf-8', errors='ignore')}")
                    if stdout:
                        logger.info(f"fbi stdout: {stdout.decode('utf-8', errors='ignore')}")
                    
                    # Restart after a delay
                    logger.info("Restarting slideshow in 5 seconds...")
                    time.sleep(5)
                    
                    # Rescan photos in case directory changed
                    self.scan_photos()
                    if not self.photos:
                        logger.error("No photos available, exiting")
                        break
                    
                    # Rebuild command with new photo list
                    cmd = [
                        'sudo', 'fbi',
                        '-T', '1',
                        '-d', '/dev/fb0',
                        '-noverbose',
                        '-a',
                        '-t', str(interval),
                        '-blend', '500',
                        '-1',  # Loop forever
                        '--'
                    ] + self.photos
                    
                    # Start new process
                    self.fbi_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    logger.info("Slideshow restarted")
                else:
                    # Process is running, wait a bit
                    time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Slideshow interrupted")
            self.stop()
        except Exception as e:
            logger.error(f"Error running slideshow: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.stop()
    
    def stop(self):
        """Stop the slideshow"""
        self.running = False
        if self.fbi_process:
            self.fbi_process.terminate()
            time.sleep(1)
            if self.fbi_process.poll() is None:
                self.fbi_process.kill()
        subprocess.run(['sudo', 'pkill', 'fbi'], capture_output=True)
        logger.info("Slideshow stopped")
    
    def create_test_image(self):
        """Create a test image if no photos exist"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Get absolute path to photos directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            photo_dir = os.path.join(script_dir, self.config['photos']['directory'])
            
            # Create test image
            img = Image.new('RGB', (800, 480), color='red')
            draw = ImageDraw.Draw(img)
            
            # Draw text
            text = "RPIFrame Test Image\nAdd photos to see slideshow"
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                font = None
            
            # Calculate text position
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width = 400
                text_height = 100
            
            x = (800 - text_width) // 2
            y = (480 - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font, align='center')
            
            # Save test image with absolute path
            os.makedirs(photo_dir, exist_ok=True)
            test_image_path = os.path.join(photo_dir, 'test_image.jpg')
            img.save(test_image_path)
            logger.info(f"Created test image at: {test_image_path}")
            
        except Exception as e:
            logger.error(f"Could not create test image: {e}")

def main():
    """Main entry point"""
    slideshow = SimpleSlideshow()
    
    # Handle signals
    def signal_handler(sig, frame):
        logger.info("Received signal, stopping slideshow")
        slideshow.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run slideshow
    slideshow.run()

if __name__ == '__main__':
    main()