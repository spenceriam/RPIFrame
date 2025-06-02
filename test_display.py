#!/usr/bin/env python3
"""
Test script for DSI display functionality with Pygame.
Tests basic display output and touch input on Raspberry Pi DSI screen.
"""
import os
import sys
import pygame
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_display():
    """Test basic display functionality"""
    try:
        # Initialize Pygame
        pygame.init()
        
        # Set up display
        # Use SDL environment variables for DSI display
        os.environ['SDL_FBDEV'] = '/dev/fb0'
        
        # Get display info
        info = pygame.display.Info()
        logger.info(f"Display info: {info.current_w}x{info.current_h}")
        
        # Create display (try fullscreen first, fall back to windowed)
        try:
            screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
            logger.info("Created fullscreen display")
        except:
            screen = pygame.display.set_mode((800, 480))
            logger.info("Created windowed display")
        
        pygame.display.set_caption("RPIFrame Display Test")
        
        # Create clock for FPS
        clock = pygame.time.Clock()
        
        # Define colors
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        RED = (255, 0, 0)
        GREEN = (0, 255, 0)
        BLUE = (0, 0, 255)
        
        # Create font
        font = pygame.font.Font(None, 36)
        small_font = pygame.font.Font(None, 24)
        
        # Test patterns
        patterns = [
            ("Black Screen", BLACK),
            ("White Screen", WHITE),
            ("Red Screen", RED),
            ("Green Screen", GREEN),
            ("Blue Screen", BLUE)
        ]
        
        current_pattern = 0
        running = True
        touch_pos = None
        
        logger.info("Starting display test. Press SPACE/Touch to change pattern, ESC to exit")
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        current_pattern = (current_pattern + 1) % len(patterns)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Touch detected
                    touch_pos = event.pos
                    current_pattern = (current_pattern + 1) % len(patterns)
                    logger.info(f"Touch detected at {touch_pos}")
            
            # Clear screen with current pattern
            pattern_name, pattern_color = patterns[current_pattern]
            screen.fill(pattern_color)
            
            # Draw pattern name
            text_color = BLACK if pattern_color == WHITE else WHITE
            text = font.render(pattern_name, True, text_color)
            text_rect = text.get_rect(center=(400, 100))
            screen.blit(text, text_rect)
            
            # Draw instructions
            inst1 = small_font.render("Touch/SPACE: Next Pattern", True, text_color)
            inst2 = small_font.render("ESC: Exit", True, text_color)
            screen.blit(inst1, (10, 440))
            screen.blit(inst2, (10, 460))
            
            # Draw touch position if available
            if touch_pos:
                pos_text = small_font.render(f"Last touch: {touch_pos}", True, text_color)
                screen.blit(pos_text, (10, 10))
                # Draw crosshair at touch position
                pygame.draw.line(screen, text_color, 
                               (touch_pos[0] - 10, touch_pos[1]), 
                               (touch_pos[0] + 10, touch_pos[1]), 2)
                pygame.draw.line(screen, text_color, 
                               (touch_pos[0], touch_pos[1] - 10), 
                               (touch_pos[0], touch_pos[1] + 10), 2)
            
            # Draw border
            pygame.draw.rect(screen, text_color, (0, 0, 800, 480), 2)
            
            # Update display
            pygame.display.flip()
            
            # Control frame rate
            clock.tick(30)
        
        logger.info("Display test completed successfully")
        
    except Exception as e:
        logger.error(f"Display test failed: {e}")
        return False
    
    finally:
        pygame.quit()
    
    return True

def test_image_display():
    """Test displaying an actual image"""
    try:
        pygame.init()
        
        # Create a test image if none exists
        test_image_path = "test_image.png"
        if not os.path.exists(test_image_path):
            logger.info("Creating test image...")
            # Create a gradient test image
            test_surface = pygame.Surface((800, 480))
            for y in range(480):
                color_val = int((y / 480) * 255)
                pygame.draw.line(test_surface, (color_val, 0, 255 - color_val), 
                               (0, y), (800, y))
            pygame.image.save(test_surface, test_image_path)
        
        # Set up display
        screen = pygame.display.set_mode((800, 480))
        pygame.display.set_caption("RPIFrame Image Test")
        
        # Load and display image
        image = pygame.image.load(test_image_path)
        screen.blit(image, (0, 0))
        pygame.display.flip()
        
        logger.info("Displaying test image. Press any key to exit...")
        
        # Wait for input
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in [pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    waiting = False
        
        return True
        
    except Exception as e:
        logger.error(f"Image display test failed: {e}")
        return False
    
    finally:
        pygame.quit()

def main():
    """Run all display tests"""
    logger.info("RPIFrame Display Test Suite")
    logger.info("=" * 40)
    
    # Check if running on Raspberry Pi
    is_pi = False
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' in model:
                is_pi = True
                logger.info(f"Running on: {model.strip()}")
    except:
        logger.warning("Not running on Raspberry Pi - some features may not work")
    
    # Run tests
    tests = [
        ("Basic Display Test", test_display),
        ("Image Display Test", test_image_display)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 40)
        
        success = test_func()
        
        if success:
            logger.info(f"✓ {test_name} PASSED")
        else:
            logger.error(f"✗ {test_name} FAILED")
    
    logger.info("\nTest suite completed")

if __name__ == '__main__':
    main()