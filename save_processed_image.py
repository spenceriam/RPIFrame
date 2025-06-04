#!/usr/bin/env python3
"""
Save the processed image to see exactly what we're displaying
"""
import os
import sys
sys.path.insert(0, '/home/spencer/RPIFrame')

from rpiframe.display import DisplayManager
from rpiframe.config import Config

# Load config
config = Config()

# Create display manager but don't initialize pygame
display_manager = DisplayManager(config)

# Pick the first photo
photo_path = "/home/spencer/RPIFrame/photos/0261.jpg"  # One we debugged above

print(f"Processing: {photo_path}")

# Process the image exactly like the display manager does
result = display_manager.load_and_process_image(photo_path)

if result:
    pygame_image, position = result
    print(f"Pygame surface size: {pygame_image.get_size()}")
    print(f"Position: {position}")
    
    # Convert pygame surface back to PIL to save it
    import pygame
    from PIL import Image
    
    # Convert pygame surface to PIL image
    w, h = pygame_image.get_size()
    raw = pygame.image.tostring(pygame_image, 'RGB')
    pil_img = Image.frombytes('RGB', (w, h), raw)
    
    # Save the processed image
    output_path = "/home/spencer/RPIFrame/processed_output.jpg"
    pil_img.save(output_path, 'JPEG', quality=95)
    print(f"Saved processed image to: {output_path}")
    print("Check this image - it should look correct and not stretched!")
    
else:
    print("Failed to process image")