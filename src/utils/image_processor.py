#!/usr/bin/env python3
"""
Image processing utilities for RPIFrame.
Handles image optimization for DSI display.
"""
import os
import logging
import subprocess
from typing import Optional, Tuple
from PIL import Image, ImageOps, ImageEnhance

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Handles image processing for the photo frame"""
    
    def __init__(self, config: dict):
        """Initialize image processor
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.display_width = config['display']['resolution']['width']
        self.display_height = config['display']['resolution']['height']
        self.photos_dir = config['photos']['directory']
        self.thumbnail_size = config['photos'].get('thumbnail_size', 200)
        self.max_dimension = config['photos'].get('max_dimension', 1920)
        self.supported_formats = config['photos'].get('supported_formats', 
            ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'heic', 'heif'])
        
    def process_new_image(self, input_path: str) -> Optional[str]:
        """Process a newly uploaded image
        
        Args:
            input_path: Path to the uploaded image
            
        Returns:
            Path to the processed image, or None if failed
        """
        try:
            # Get the base filename without extension
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            
            # Check if it's a HEIC/HEIF file
            if input_path.lower().endswith(('.heic', '.heif')):
                # Convert HEIC to JPEG using ImageMagick
                temp_path = os.path.join(os.path.dirname(input_path), f"{base_name}_converted.jpg")
                result = subprocess.run(
                    ['convert', input_path, temp_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to convert HEIC image: {result.stderr}")
                    return None
                
                # Use the converted file
                input_path = temp_path
            
            # Open the image
            img = Image.open(input_path)
            
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Remove EXIF orientation and apply it to the image
            img = ImageOps.exif_transpose(img)
            
            # Resize if too large (to save storage)
            if max(img.size) > self.max_dimension:
                img.thumbnail((self.max_dimension, self.max_dimension), Image.Resampling.LANCZOS)
            
            # Save the processed image
            output_path = os.path.join(self.photos_dir, f"{base_name}.jpg")
            img.save(output_path, 'JPEG', quality=90, optimize=True)
            
            # Create thumbnail
            self.create_thumbnail(img, base_name)
            
            # Clean up temporary files
            if 'temp_path' in locals():
                os.remove(temp_path)
            if input_path != output_path:
                os.remove(input_path)
            
            logger.info(f"Processed image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None
    
    def create_thumbnail(self, img: Image.Image, base_name: str) -> bool:
        """Create a thumbnail for the web interface
        
        Args:
            img: PIL Image object
            base_name: Base filename without extension
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create thumbnails directory
            thumbs_dir = os.path.join(self.photos_dir, 'thumbnails')
            os.makedirs(thumbs_dir, exist_ok=True)
            
            # Create thumbnail
            thumb = img.copy()
            thumb.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
            
            # Save thumbnail
            thumb_path = os.path.join(thumbs_dir, f"{base_name}.jpg")
            thumb.save(thumb_path, 'JPEG', quality=85, optimize=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return False
    
    def prepare_for_display(self, image_path: str, rotation: int = 0, 
                          fit_mode: str = 'contain') -> Image.Image:
        """Prepare an image for display on the DSI screen
        
        Args:
            image_path: Path to the image file
            rotation: Rotation angle (0, 90, 180, 270)
            fit_mode: How to fit the image ('contain', 'cover', 'stretch')
            
        Returns:
            Prepared PIL Image object
        """
        try:
            # Open the image
            img = Image.open(image_path)
            
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Apply rotation if specified
            if rotation in (90, 180, 270):
                img = img.rotate(-rotation, expand=True)
            
            # Resize based on fit mode
            if fit_mode == 'contain':
                # Fit inside display (preserve aspect ratio)
                img.thumbnail((self.display_width, self.display_height), Image.Resampling.LANCZOS)
                
                # Create black background
                background = Image.new('RGB', (self.display_width, self.display_height), (0, 0, 0))
                
                # Paste image centered
                x = (self.display_width - img.width) // 2
                y = (self.display_height - img.height) // 2
                background.paste(img, (x, y))
                img = background
                
            elif fit_mode == 'cover':
                # Fill display (may crop)
                img = self._resize_cover(img, self.display_width, self.display_height)
                
            elif fit_mode == 'stretch':
                # Stretch to fill (may distort)
                img = img.resize((self.display_width, self.display_height), Image.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            logger.error(f"Error preparing image for display: {e}")
            # Return a black image on error
            return Image.new('RGB', (self.display_width, self.display_height), (0, 0, 0))
    
    def _resize_cover(self, img: Image.Image, width: int, height: int) -> Image.Image:
        """Resize image to cover the target area (may crop)
        
        Args:
            img: Source image
            width: Target width
            height: Target height
            
        Returns:
            Resized image
        """
        # Calculate scale factors
        scale_x = width / img.width
        scale_y = height / img.height
        scale = max(scale_x, scale_y)
        
        # Resize image
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to target size
        left = (new_width - width) // 2
        top = (new_height - height) // 2
        right = left + width
        bottom = top + height
        
        return img.crop((left, top, right, bottom))
    
    def enhance_image(self, img: Image.Image, brightness: float = 1.0, 
                     contrast: float = 1.0, saturation: float = 1.0) -> Image.Image:
        """Enhance image with brightness, contrast, and saturation adjustments
        
        Args:
            img: PIL Image object
            brightness: Brightness factor (1.0 = no change)
            contrast: Contrast factor (1.0 = no change)
            saturation: Saturation factor (1.0 = no change)
            
        Returns:
            Enhanced image
        """
        try:
            # Apply brightness
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(brightness)
            
            # Apply contrast
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast)
            
            # Apply saturation
            if saturation != 1.0:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(saturation)
            
            return img
            
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return img