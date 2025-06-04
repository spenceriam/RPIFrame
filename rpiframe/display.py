"""
Display manager for RPIFrame DSI touchscreen.
Handles photo slideshow, touch input, and display control.
"""

import os
import sys
import glob
import time
import logging
import random
from pathlib import Path
from typing import List, Tuple, Optional, TYPE_CHECKING

try:
    import pygame
    from PIL import Image, ImageOps
    DISPLAY_AVAILABLE = True
except ImportError as e:
    DISPLAY_AVAILABLE = False
    pygame = None
    Image = None
    logging.getLogger(__name__).warning(f"Display dependencies not available: {e}")

if TYPE_CHECKING:
    from .config import Config

logger = logging.getLogger(__name__)

class DisplayManager:
    """Manages photo slideshow on DSI display with touch controls"""
    
    def __init__(self, config: 'Config'):
        """Initialize display manager"""
        if not DISPLAY_AVAILABLE:
            raise ImportError("Display dependencies (pygame, PIL) not available")
        
        self.config = config
        self.running = False
        self.current_photo_index = 0
        self.photos: List[str] = []
        self.last_photo_update = 0
        self.screen = None
        self.clock = None
        
        # Display settings
        self.width = self.config.display.get("width", 800)
        self.height = self.config.display.get("height", 480)
        self.rotation = self.config.display.get("rotation", 0)
        self.slideshow_interval = self.config.display.get("slideshow_interval", 60)
        self.fit_mode = self.config.display.get("fit_mode", "contain")
        self.enable_touch = self.config.system.get("enable_touch", True)
        
        # Photo settings
        self.photo_dir = Path(self.config.photos.get("directory", "photos"))
        self.allowed_extensions = self.config.photos.get("allowed_extensions", ["jpg", "jpeg", "png"])
        
        # Touch gesture settings
        self.swipe_threshold = 50  # pixels
        self.swipe_start_pos = None
        self.swipe_start_time = None
        
        logger.info(f"DisplayManager initialized: {self.width}x{self.height}")
    
    def initialize_display(self) -> bool:
        """Initialize pygame and display"""
        try:
            if not DISPLAY_AVAILABLE:
                logger.error("Display dependencies not available")
                return False
            
            pygame.init()
            
            # Configure SDL for Raspberry Pi DSI display
            os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
            os.environ['SDL_FBDEV'] = '/dev/fb0'
            
            # Get display info
            try:
                info = pygame.display.Info()
                logger.info(f"Display info: {info.current_w}x{info.current_h}")
            except:
                logger.warning("Could not get display info")
            
            # Create fullscreen display
            flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
            self.screen = pygame.display.set_mode((self.width, self.height), flags)
            pygame.display.set_caption("RPIFrame Photo Display")
            
            # Hide mouse cursor
            pygame.mouse.set_visible(False)
            
            # Initialize clock
            self.clock = pygame.time.Clock()
            
            # Clear screen
            self.screen.fill((0, 0, 0))
            pygame.display.flip()
            
            logger.info("Display initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing display: {e}")
            return False
    
    def load_photos(self) -> bool:
        """Load photo list from directory"""
        try:
            self.photos.clear()
            
            if not self.photo_dir.exists():
                logger.warning(f"Photo directory does not exist: {self.photo_dir}")
                return False
            
            # Find all image files
            for ext in self.allowed_extensions:
                pattern = str(self.photo_dir / f"*.{ext}")
                self.photos.extend(glob.glob(pattern))
                
                # Also check uppercase extensions
                pattern = str(self.photo_dir / f"*.{ext.upper()}")
                self.photos.extend(glob.glob(pattern))
            
            # Remove duplicates and sort
            self.photos = sorted(list(set(self.photos)))
            
            logger.info(f"Loaded {len(self.photos)} photos")
            
            if not self.photos:
                logger.warning("No photos found")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading photos: {e}")
            return False
    
    def load_and_process_image(self, image_path: str):
        """Load image and process for display"""
        try:
            # Load with PIL
            pil_image = Image.open(image_path)
            
            # Convert to RGB if needed
            if pil_image.mode not in ('RGB', 'RGBA'):
                pil_image = pil_image.convert('RGB')
            
            # Apply EXIF rotation
            pil_image = ImageOps.exif_transpose(pil_image)
            
            # Apply configured rotation
            if self.rotation != 0:
                pil_image = pil_image.rotate(-self.rotation, expand=True)
            
            # Calculate scaling based on fit mode
            img_ratio = pil_image.width / pil_image.height
            display_ratio = self.width / self.height
            
            if self.fit_mode == "cover":
                # Fill entire screen, crop if necessary
                if img_ratio > display_ratio:
                    new_height = self.height
                    new_width = int(self.height * img_ratio)
                else:
                    new_width = self.width
                    new_height = int(self.width / img_ratio)
            else:  # contain (default)
                # Fit within screen, show black bars if necessary
                if img_ratio > display_ratio:
                    new_width = self.width
                    new_height = int(self.width / img_ratio)
                else:
                    new_height = self.height
                    new_width = int(self.height * img_ratio)
            
            # Resize image
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to pygame surface
            if pil_image.mode == 'RGBA':
                image_str = pil_image.tobytes()
                pygame_image = pygame.image.fromstring(image_str, pil_image.size, 'RGBA')
            else:
                image_str = pil_image.tobytes()
                pygame_image = pygame.image.fromstring(image_str, pil_image.size, 'RGB')
            
            # Calculate position to center image
            x = (self.width - new_width) // 2
            y = (self.height - new_height) // 2
            
            return pygame_image, (x, y)
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return None
    
    def display_photo(self, photo_path: str) -> bool:
        """Display a photo on screen"""
        try:
            result = self.load_and_process_image(photo_path)
            if result is None:
                return False
            
            image_surface, position = result
            
            # Clear screen
            self.screen.fill((0, 0, 0))
            
            # Draw image
            self.screen.blit(image_surface, position)
            
            # Update display
            pygame.display.flip()
            
            logger.info(f"Displayed: {Path(photo_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"Error displaying photo: {e}")
            return False
    
    def display_message(self, message: str, color=(255, 255, 255)) -> None:
        """Display a text message on screen"""
        try:
            if not pygame.font.get_init():
                pygame.font.init()
            
            font = pygame.font.Font(None, 48)
            text_surface = font.render(message, True, color)
            
            # Center text
            text_rect = text_surface.get_rect()
            text_rect.center = (self.width // 2, self.height // 2)
            
            # Clear screen and display message
            self.screen.fill((0, 0, 0))
            self.screen.blit(text_surface, text_rect)
            pygame.display.flip()
            
        except Exception as e:
            logger.error(f"Error displaying message: {e}")
    
    def handle_swipe(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]) -> None:
        """Handle swipe gesture"""
        dx = end_pos[0] - start_pos[0]
        
        if abs(dx) > self.swipe_threshold:
            if dx > 0:
                self.previous_photo()
            else:
                self.next_photo()
    
    def next_photo(self) -> None:
        """Display next photo"""
        if not self.photos:
            return
        
        self.current_photo_index = (self.current_photo_index + 1) % len(self.photos)
        self.display_photo(self.photos[self.current_photo_index])
        self.last_photo_update = time.time()
    
    def previous_photo(self) -> None:
        """Display previous photo"""
        if not self.photos:
            return
        
        self.current_photo_index = (self.current_photo_index - 1) % len(self.photos)
        self.display_photo(self.photos[self.current_photo_index])
        self.last_photo_update = time.time()
    
    def run(self) -> None:
        """Main display loop"""
        logger.info("Starting display manager")
        
        # Initialize display
        if not self.initialize_display():
            logger.error("Failed to initialize display")
            return
        
        # Load photos
        if not self.load_photos():
            self.display_message("No photos found!\nUpload photos via web interface.", (255, 100, 100))
            time.sleep(10)
            return
        
        # Display first photo
        if self.photos:
            self.display_photo(self.photos[self.current_photo_index])
            self.last_photo_update = time.time()
        
        self.running = True
        logger.info("Display slideshow started")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_SPACE:
                            self.next_photo()
                        elif event.key == pygame.K_LEFT:
                            self.previous_photo()
                        elif event.key == pygame.K_r:
                            # Reload photos
                            self.load_photos()
                    
                    elif self.enable_touch:
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            self.swipe_start_pos = event.pos
                            self.swipe_start_time = current_time
                        
                        elif event.type == pygame.MOUSEBUTTONUP and self.swipe_start_pos:
                            # Simple touch vs swipe detection
                            time_diff = current_time - (self.swipe_start_time or 0)
                            if time_diff < 0.5:  # Quick touch
                                self.handle_swipe(self.swipe_start_pos, event.pos)
                            self.swipe_start_pos = None
                
                # Auto-advance slideshow
                if current_time - self.last_photo_update >= self.slideshow_interval:
                    self.next_photo()
                
                # Reload photos periodically (every 5 minutes)
                if int(current_time) % 300 == 0:
                    old_count = len(self.photos)
                    self.load_photos()
                    if len(self.photos) != old_count:
                        logger.info(f"Photo count changed: {old_count} -> {len(self.photos)}")
                        if not self.photos:
                            self.display_message("No photos found!", (255, 100, 100))
                
                # Control frame rate
                if self.clock:
                    self.clock.tick(30)
                
        except KeyboardInterrupt:
            logger.info("Display interrupted by user")
        except Exception as e:
            logger.error(f"Error in display loop: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Clean up display resources"""
        logger.info("Cleaning up display")
        self.running = False
        
        if pygame and pygame.get_init():
            pygame.quit()
        
        logger.info("Display cleanup complete")