#!/usr/bin/env python3
"""Simple display test to diagnose black screen issue"""

import pygame
import sys
import time

def test_display():
    print("Initializing pygame...")
    pygame.init()
    
    # Get display info
    info = pygame.display.Info()
    print(f"Display detected: {info.current_w}x{info.current_h}")
    
    # Try different display modes
    modes = [
        (800, 480),  # Expected DSI display size
        (1024, 768),  # What pygame is detecting
        (0, 0),  # Fullscreen
    ]
    
    for width, height in modes:
        try:
            print(f"\nTrying mode: {width}x{height}")
            
            if width == 0:
                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                actual_size = screen.get_size()
                print(f"Fullscreen mode: {actual_size}")
            else:
                screen = pygame.display.set_mode((width, height))
                print(f"Set mode: {width}x{height}")
            
            # Fill with different colors
            colors = [
                ((255, 0, 0), "RED"),
                ((0, 255, 0), "GREEN"),
                ((0, 0, 255), "BLUE"),
                ((255, 255, 255), "WHITE")
            ]
            
            for color, name in colors:
                print(f"Displaying {name}")
                screen.fill(color)
                
                # Add text
                font = pygame.font.Font(None, 36)
                text = font.render(f"RPIFrame Test - {name}", True, (0, 0, 0) if name == "WHITE" else (255, 255, 255))
                text_rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
                screen.blit(text, text_rect)
                
                pygame.display.flip()
                time.sleep(2)
            
            # Wait for key press
            print("Press any key to try next mode...")
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                        waiting = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        print(f"Touch detected at: {event.pos}")
                        waiting = False
                time.sleep(0.1)
            
        except Exception as e:
            print(f"Error with mode {width}x{height}: {e}")
            continue
    
    pygame.quit()
    print("\nTest complete!")

if __name__ == "__main__":
    test_display()