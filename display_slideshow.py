#!/usr/bin/env python3
"""
DSI Display Slideshow for RPIFrame.
Handles photo display on the Hosyond 7-inch DSI IPS touchscreen.
Supports full-color display, rotation control, and touch navigation.
"""
import os
import sys
import json
import glob
import time
import logging
import random
import threading
from datetime import datetime

import pygame
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rpiframe_display.log')
    ]
)

logger = logging.getLogger(__name__)

class PhotoSlideshow:
    """Manages photo slideshow on DSI display with touch controls"""
    
    def __init__(self, config_file='config.json'):
        """Initialize the slideshow manager"""
        self.config = self.load_config(config_file)
        self.running = False
        self.current_photo_index = 0
        self.photos = []
        self.last_photo_update = 0
        self.screen = None
        self.clock = None
        
        # Display settings
        self.width = self.config['display']['width']
        self.height = self.config['display']['height']
        self.rotation = self.config['display']['rotation']
        self.slideshow_interval = self.config['display']['slideshow_interval']
        self.enable_touch = self.config['system']['enable_touch']
        
        # Photo directory
        self.photo_dir = self.config['photos']['directory']
        self.allowed_extensions = self.config['photos']['allowed_extensions']
        
        # Touch gesture settings
        self.swipe_threshold = 50  # pixels
        self.swipe_start_pos = None
        self.swipe_start_time = None
        
    def load_config(self, config_file):
        """Load configuration from file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Return default config
            return {
                "display": {
                    "width": 800,
                    "height": 480,
                    "rotation": 0,
                    "slideshow_interval": 60,
                    "transition_effect": "fade"
                },
                "photos": {
                    "directory": "photos",
                    "allowed_extensions": ["png", "jpg", "jpeg", "gif", "bmp"]
                },
                "system": {
                    "enable_touch": True
                }
            }
    
    def initialize_display(self):
        """Initialize Pygame and the display"""
        try:
            pygame.init()
            
            # Set up display for Hosyond 7-inch DSI (800x480, FT5426 touch)
            # Use KMS driver for Pi 4 with FKMS mode
            os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
            os.environ['SDL_FBDEV'] = '/dev/fb0'
            
            # Initialize display
            info = pygame.display.Info()
            logger.info(f"Display info: {info.current_w}x{info.current_h}")
            
            # Create fullscreen display
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
            pygame.display.set_caption("RPIFrame Photo Display")
            
            # Hide mouse cursor
            pygame.mouse.set_visible(False)
            
            # Initialize clock for FPS control
            self.clock = pygame.time.Clock()
            
            logger.info(f"Display initialized: {self.width}x{self.height}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing display: {e}")
            return False
    
    def load_photos(self):
        """Load list of photos from directory"""
        self.photos = []
        
        try:
            for ext in self.allowed_extensions:
                pattern = os.path.join(self.photo_dir, f'*.{ext}')
                self.photos.extend(glob.glob(pattern))
            
            # Sort photos by name
            self.photos.sort()
            
            logger.info(f"Loaded {len(self.photos)} photos")
            
            if not self.photos:
                logger.warning("No photos found in directory")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading photos: {e}")
            return False
    
    def load_and_scale_image(self, image_path):
        """Load an image and scale it to fit the display"""
        try:
            # Load image with PIL
            pil_image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Apply rotation if configured
            if self.rotation != 0:
                pil_image = pil_image.rotate(-self.rotation, expand=True)
            
            # Calculate scaling to fit display while maintaining aspect ratio
            img_ratio = pil_image.width / pil_image.height
            display_ratio = self.width / self.height
            
            if img_ratio > display_ratio:
                # Image is wider - scale by width
                new_width = self.width
                new_height = int(self.width / img_ratio)
            else:
                # Image is taller - scale by height
                new_height = self.height
                new_width = int(self.height * img_ratio)
            
            # Resize image
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to pygame surface
            image_str = pil_image.tobytes()
            image_surface = pygame.image.fromstring(image_str, pil_image.size, pil_image.mode)
            
            # Center the image on screen
            x = (self.width - new_width) // 2
            y = (self.height - new_height) // 2
            
            return image_surface, (x, y)
            
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None, None
    
    def display_photo(self, photo_path):
        """Display a photo on the screen"""
        try:
            # Load and scale the image
            image_surface, position = self.load_and_scale_image(photo_path)
            
            if image_surface is None:
                return False
            
            # Clear screen with black background
            self.screen.fill((0, 0, 0))
            
            # Display the image
            self.screen.blit(image_surface, position)
            
            # Update display
            pygame.display.flip()
            
            logger.info(f"Displayed photo: {os.path.basename(photo_path)}")
            return True
            
        except Exception as e:
            logger.error(f"Error displaying photo: {e}")
            return False
    
    def handle_swipe(self, start_pos, end_pos):
        """Handle swipe gesture"""
        dx = end_pos[0] - start_pos[0]
        
        if abs(dx) > self.swipe_threshold:
            if dx > 0:
                # Swipe right - previous photo
                self.previous_photo()
            else:
                # Swipe left - next photo
                self.next_photo()
    
    def next_photo(self):
        """Display next photo"""
        if not self.photos:
            return
            
        self.current_photo_index = (self.current_photo_index + 1) % len(self.photos)
        self.display_photo(self.photos[self.current_photo_index])
        self.last_photo_update = time.time()
    
    def previous_photo(self):
        """Display previous photo"""
        if not self.photos:
            return
            
        self.current_photo_index = (self.current_photo_index - 1) % len(self.photos)
        self.display_photo(self.photos[self.current_photo_index])
        self.last_photo_update = time.time()
    
    def run(self):
        """Main slideshow loop"""
        # Initialize display
        if not self.initialize_display():
            logger.error("Failed to initialize display")
            return
        
        # Load photos
        if not self.load_photos():
            logger.error("No photos to display")
            return
        
        # Display first photo
        if self.photos:
            self.display_photo(self.photos[self.current_photo_index])
            self.last_photo_update = time.time()
        
        self.running = True
        logger.info("Starting slideshow")
        
        try:
            while self.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_RIGHT:
                            self.next_photo()
                        elif event.key == pygame.K_LEFT:
                            self.previous_photo()
                    
                    elif self.enable_touch:
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            self.swipe_start_pos = event.pos
                            self.swipe_start_time = time.time()
                        
                        elif event.type == pygame.MOUSEBUTTONUP:
                            if self.swipe_start_pos:
                                self.handle_swipe(self.swipe_start_pos, event.pos)
                                self.swipe_start_pos = None
                
                # Check if it's time to advance slideshow
                current_time = time.time()
                if current_time - self.last_photo_update >= self.slideshow_interval:
                    self.next_photo()
                
                # Reload photos periodically to pick up new uploads
                if int(current_time) % 300 == 0:  # Every 5 minutes
                    old_count = len(self.photos)
                    self.load_photos()
                    if len(self.photos) != old_count:
                        logger.info(f"Photo count changed: {old_count} -> {len(self.photos)}")
                
                # Control frame rate
                self.clock.tick(30)  # 30 FPS
                
        except KeyboardInterrupt:
            logger.info("Slideshow interrupted by user")
        except Exception as e:
            logger.error(f"Error in slideshow loop: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up...")
        pygame.quit()
        self.running = False

def main():
    """Main entry point"""
    slideshow = PhotoSlideshow()
    
    try:
        slideshow.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()