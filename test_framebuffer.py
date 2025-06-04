#!/usr/bin/env python3
"""Test display using framebuffer directly"""

import os
import pygame
import time

# Set SDL to use framebuffer
os.environ['SDL_VIDEODRIVER'] = 'fbcon'
os.environ['SDL_FBDEV'] = '/dev/fb0'

print("Testing framebuffer display...")
print(f"SDL_VIDEODRIVER: {os.environ.get('SDL_VIDEODRIVER')}")
print(f"SDL_FBDEV: {os.environ.get('SDL_FBDEV')}")

try:
    pygame.init()
    
    # Try to create display
    info = pygame.display.Info()
    print(f"Display info: {info.current_w}x{info.current_h}")
    
    # Create screen
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    print(f"Screen created: {screen.get_size()}")
    
    # Simple color test
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
    for color in colors:
        screen.fill(color)
        pygame.display.flip()
        print(f"Displaying color: {color}")
        time.sleep(1)
    
    pygame.quit()
    print("Test successful!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()