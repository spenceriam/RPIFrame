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
        # Get interval from web settings (in minutes) or fallback to legacy (in seconds)
        rotation_interval_minutes = self.config.display.get("rotation_interval_minutes")
        if rotation_interval_minutes:
            self.slideshow_interval = rotation_interval_minutes * 60  # Convert to seconds
        else:
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
            
            # Try different SDL drivers for Raspberry Pi DSI display
            drivers_to_try = [
                ('x11', {}),
                ('fbcon', {'SDL_FBDEV': '/dev/fb0'}),
                ('directfb', {}),
                ('kmsdrm', {'SDL_FBDEV': '/dev/fb0'}),
                (None, {})  # Default driver
            ]
            
            initialized = False
            for driver, env_vars in drivers_to_try:
                try:
                    # Set environment variables
                    if driver:
                        os.environ['SDL_VIDEODRIVER'] = driver
                    else:
                        os.environ.pop('SDL_VIDEODRIVER', None)
                    
                    for key, value in env_vars.items():
                        os.environ[key] = value
                    
                    # Try to initialize pygame
                    pygame.init()
                    
                    # Test if we can get display info
                    info = pygame.display.Info()
                    logger.info(f"Initialized with driver: {driver or 'default'}, Display: {info.current_w}x{info.current_h}")
                    initialized = True
                    break
                    
                except Exception as e:
                    logger.debug(f"Failed with driver {driver}: {e}")
                    pygame.quit()
                    # Clean up environment
                    os.environ.pop('SDL_VIDEODRIVER', None)
                    for key in env_vars:
                        os.environ.pop(key, None)
                    continue
            
            if not initialized:
                raise Exception("Could not initialize display with any driver")
            
            # Create fullscreen display
            flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
            
            # First try to get the actual display info
            info = pygame.display.Info()
            actual_width, actual_height = info.current_w, info.current_h
            logger.info(f"Actual display resolution: {actual_width}x{actual_height}")
            logger.info(f"Requested resolution: {self.width}x{self.height}")
            
            # Use actual display resolution if it's different from config
            if actual_width != self.width or actual_height != self.height:
                logger.warning(f"Display resolution mismatch! Using actual: {actual_width}x{actual_height}")
                self.width = actual_width
                self.height = actual_height
            
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
            
            # Get original dimensions BEFORE any squishing
            orig_width, orig_height = pil_image.size
            img_ratio = orig_width / orig_height
            display_ratio = self.width / self.height
            
            logger.info(f"Original image size: {orig_width}x{orig_height} (ratio: {img_ratio:.3f})")
            logger.info(f"Display ratio: {display_ratio:.3f}")
            
            logger.info(f"Processing image: {orig_width}x{orig_height} (ratio: {img_ratio:.2f}) for display: {self.width}x{self.height} (ratio: {display_ratio:.2f})")
            
            if self.fit_mode == "cover":
                # COVER MODE: Fill entire screen with proper centering
                # Step 1: Determine center crop area based on ORIGINAL image dimensions
                
                if img_ratio > display_ratio:
                    # Image is wider than display ratio - crop horizontally (keep full height)
                    target_width = int(orig_height * display_ratio)
                    target_height = orig_height
                    crop_left = (orig_width - target_width) // 2
                    crop_top = 0
                else:
                    # Image is taller than display ratio - crop vertically (keep full width)  
                    target_width = orig_width
                    target_height = int(orig_width / display_ratio)
                    crop_left = 0
                    crop_top = (orig_height - target_height) // 2
                
                crop_right = crop_left + target_width
                crop_bottom = crop_top + target_height
                
                logger.info(f"Step 1 - Center crop based on original: ({crop_left}, {crop_top}, {crop_right}, {crop_bottom})")
                logger.info(f"Cropping from {orig_width}x{orig_height} to {target_width}x{target_height}")
                
                # Apply the center crop
                pil_image = pil_image.crop((crop_left, crop_top, crop_right, crop_bottom))
                
                # Step 2: Apply counter-squish to the cropped image
                squish_factor = 0.9
                squished_width = int(pil_image.size[0] * squish_factor)
                squished_height = pil_image.size[1]
                
                logger.info(f"Step 2 - Counter-squish: {pil_image.size[0]}x{pil_image.size[1]} → {squished_width}x{squished_height} (factor: {squish_factor})")
                
                pil_image = pil_image.resize((squished_width, squished_height), Image.Resampling.LANCZOS)
                
                # Step 3: Scale to final display size
                final_scale_x = self.width / squished_width
                final_scale_y = self.height / squished_height
                final_scale = max(final_scale_x, final_scale_y)  # Ensure we fill the screen
                
                final_width = int(squished_width * final_scale)
                final_height = int(squished_height * final_scale)
                
                logger.info(f"Step 3 - Final scale: {final_scale:.3f}, Final size: {final_width}x{final_height}")
                
                pil_image = pil_image.resize((final_width, final_height), Image.Resampling.LANCZOS)
                
                # Step 4: Final crop to exact display size if needed
                if final_width > self.width or final_height > self.height:
                    final_crop_left = max(0, (final_width - self.width) // 2)
                    final_crop_top = max(0, (final_height - self.height) // 2)
                    final_crop_right = final_crop_left + self.width
                    final_crop_bottom = final_crop_top + self.height
                    
                    logger.info(f"Step 4 - Final crop: ({final_crop_left}, {final_crop_top}, {final_crop_right}, {final_crop_bottom})")
                    pil_image = pil_image.crop((final_crop_left, final_crop_top, final_crop_right, final_crop_bottom))
                
                # Position at top-left
                x, y = 0, 0
                
            else:  # contain (default)
                # CONTAIN MODE: Fit within screen, show black bars if necessary, maintain aspect ratio
                scale_for_width = self.width / orig_width
                scale_for_height = self.height / orig_height
                
                logger.info(f"Scale factors: width={scale_for_width:.6f}, height={scale_for_height:.6f}")
                
                # Use the SMALLER scale factor to ensure we fit within the screen
                scale_factor = min(scale_for_width, scale_for_height)
                logger.info(f"Using min scale factor: {scale_factor:.6f}")
                
                new_width = int(orig_width * scale_factor)
                new_height = int(orig_height * scale_factor)
                
                logger.info(f"Scaled dimensions: {new_width}x{new_height}")
                
                # Resize image
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Calculate position to center image
                x = (self.width - new_width) // 2
                y = (self.height - new_height) // 2
                
                logger.info(f"Centering at position: ({x}, {y})")
                logger.info(f"Black bars: left/right={x}px, top/bottom={y}px")
            
            # Convert to pygame surface
            if pil_image.mode == 'RGBA':
                image_str = pil_image.tobytes()
                pygame_image = pygame.image.fromstring(image_str, pil_image.size, 'RGBA')
            else:
                image_str = pil_image.tobytes()
                pygame_image = pygame.image.fromstring(image_str, pil_image.size, 'RGB')
            
            # Verify final image dimensions match what we expect
            final_size = pygame_image.get_size()
            logger.info(f"Final pygame surface size: {final_size[0]}x{final_size[1]}, position: ({x}, {y})")
            
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
            surface_size = image_surface.get_size()
            screen_size = self.screen.get_size()
            
            logger.info(f"Screen size: {screen_size}, Image surface size: {surface_size}, Position: {position}")
            
            # Verify sizes match expectations
            if surface_size != (self.width, self.height):
                logger.warning(f"Size mismatch! Surface: {surface_size}, Expected: {(self.width, self.height)}")
            
            # Clear screen
            self.screen.fill((0, 0, 0))
            
            # Draw image - NO scaling, direct blit
            self.screen.blit(image_surface, position)
            
            # Update display
            pygame.display.flip()
            
            # Update current photo indicator for web interface
            try:
                current_file = Path('/tmp/rpiframe_current_photo')
                current_file.write_text(Path(photo_path).name)
            except Exception as e:
                logger.warning(f"Failed to update current photo indicator: {e}")
            
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
        
        # Display first photo (start with random photo)
        if self.photos:
            self.current_photo_index = random.randint(0, len(self.photos) - 1)
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
                
                # Check for next photo signal from web interface
                signal_file = Path('/tmp/rpiframe_next_photo')
                if signal_file.exists():
                    try:
                        signal_file.unlink()  # Remove the signal file
                        self.next_photo()
                        logger.info("Advanced to next photo via web interface")
                    except Exception as e:
                        logger.error(f"Error processing next photo signal: {e}")
                
                # Auto-advance slideshow
                if current_time - self.last_photo_update >= self.slideshow_interval:
                    self.next_photo()
                
                # Reload photos periodically (every 5 minutes)
                if not hasattr(self, 'last_photo_reload'):
                    self.last_photo_reload = current_time
                
                if current_time - self.last_photo_reload >= 300:  # 5 minutes
                    old_count = len(self.photos)
                    self.load_photos()
                    self.last_photo_reload = current_time
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