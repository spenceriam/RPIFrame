#!/usr/bin/env python3
"""
Quick test to display the test pattern immediately
"""
import os
import sys
import time
os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
os.environ['SDL_FBDEV'] = '/dev/fb0'

# Add the rpiframe module to path
sys.path.insert(0, '/home/spencer/RPIFrame')

try:
    import pygame
    from PIL import Image
    
    pygame.init()
    
    # Set up display - try both resolutions
    print("Testing display resolutions...")
    
    # Try 800x480 first
    try:
        screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
        print("✓ Using 800x480 mode")
        width, height = 800, 480
    except Exception as e:
        print(f"✗ 800x480 failed: {e}")
        try:
            screen = pygame.display.set_mode((1024, 600), pygame.FULLSCREEN)
            print("✓ Using 1024x600 mode")
            width, height = 1024, 600
        except Exception as e2:
            print(f"✗ 1024x600 also failed: {e2}")
            sys.exit(1)
    
    print(f"Screen size: {screen.get_size()}")
    
    # Load and display test pattern
    test_image = Image.open('/home/spencer/RPIFrame/photos/test_pattern.jpg')
    print(f"Test image size: {test_image.size}")
    
    # Convert to pygame surface - NO SCALING
    image_str = test_image.tobytes()
    pygame_image = pygame.image.fromstring(image_str, test_image.size, 'RGB')
    
    # Clear screen and display
    screen.fill((0, 0, 0))
    screen.blit(pygame_image, (0, 0))
    pygame.display.flip()
    
    print("Test pattern displayed for 10 seconds...")
    print("Check if squares appear as squares and circles as circles!")
    time.sleep(10)
    
    pygame.quit()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()