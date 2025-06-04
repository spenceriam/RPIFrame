#!/usr/bin/env python3
"""
Display wrapper that chooses between pygame and fbi slideshow
"""
import subprocess
import sys
import os

def test_pygame():
    """Test if pygame display works"""
    try:
        import pygame
        pygame.init()
        pygame.display.init()
        pygame.display.set_mode((100, 100))
        pygame.quit()
        return True
    except:
        return False

def main():
    """Run appropriate display method"""
    if test_pygame():
        print("Using pygame display")
        import display_slideshow
        slideshow = display_slideshow.PhotoSlideshow()
        slideshow.run()
    else:
        print("Using fbi framebuffer display")
        import simple_slideshow
        slideshow = simple_slideshow.SimpleSlideshow()
        slideshow.run()

if __name__ == '__main__':
    main()
