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

logging.basicConfig(level=logging.INFO)
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
        photo_dir = self.config['photos']['directory']
        
        if not os.path.exists(photo_dir):
            os.makedirs(photo_dir)
            logger.warning(f"Created photos directory: {photo_dir}")
            return
        
        for ext in self.config['photos']['allowed_extensions']:
            pattern = os.path.join(photo_dir, f'*.{ext}')
            self.photos.extend(glob.glob(pattern))
            pattern = os.path.join(photo_dir, f'*.{ext.upper()}')
            self.photos.extend(glob.glob(pattern))
        
        self.photos.sort()
        logger.info(f"Found {len(self.photos)} photos")
    
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
            '--'  # End of options
        ] + self.photos
        
        logger.info(f"Starting slideshow with {len(self.photos)} photos")
        logger.info(f"Slideshow interval: {interval} seconds")
        
        try:
            # Start fbi
            self.fbi_process = subprocess.Popen(cmd)
            logger.info("Slideshow started successfully")
            
            # Wait for process to complete or be interrupted
            self.fbi_process.wait()
            
        except KeyboardInterrupt:
            logger.info("Slideshow interrupted")
            self.stop()
        except Exception as e:
            logger.error(f"Error running slideshow: {e}")
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
            
            # Save test image
            os.makedirs('photos', exist_ok=True)
            img.save('photos/test_image.jpg')
            logger.info("Created test image")
            
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