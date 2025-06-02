#!/usr/bin/env python3
"""
RPIFrame Display Diagnostics
Tests SDL2 video drivers and display configuration
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables"""
    logger.info("=== Environment Variables ===")
    important_vars = [
        'SDL_VIDEODRIVER', 'DISPLAY', 'SDL_FBDEV', 
        'HOME', 'USER', 'PYTHONPATH'
    ]
    for var in important_vars:
        value = os.environ.get(var, 'Not set')
        logger.info(f"  {var}: {value}")
    print()

def check_display_devices():
    """Check available display devices"""
    logger.info("=== Display Devices ===")
    
    # Check DRM devices
    try:
        drm_devices = os.listdir('/dev/dri/')
        logger.info(f"DRM devices: {drm_devices}")
    except:
        logger.error("No /dev/dri/ directory found")
    
    # Check framebuffer devices
    fb_devices = [f for f in os.listdir('/dev/') if f.startswith('fb')]
    if fb_devices:
        logger.info(f"Framebuffer devices: {fb_devices}")
        for fb in fb_devices:
            try:
                with open(f'/sys/class/graphics/{fb}/name', 'r') as f:
                    name = f.read().strip()
                    logger.info(f"  {fb}: {name}")
            except:
                pass
    else:
        logger.error("No framebuffer devices found")
    
    # Check video groups
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        logger.info(f"User groups: {result.stdout.strip()}")
    except:
        pass
    print()

def check_sdl_info():
    """Check SDL2 installation and configuration"""
    logger.info("=== SDL2 Information ===")
    
    # Check SDL2 version
    try:
        result = subprocess.run(['sdl2-config', '--version'], capture_output=True, text=True)
        logger.info(f"SDL2 version: {result.stdout.strip()}")
    except:
        logger.warning("sdl2-config not found")
    
    # Check pygame
    try:
        import pygame
        logger.info(f"Pygame version: {pygame.ver}")
        logger.info(f"SDL version: {pygame.get_sdl_version()}")
    except ImportError:
        logger.error("Pygame not installed")
        return
    print()

def test_video_drivers():
    """Test each video driver"""
    logger.info("=== Testing Video Drivers ===")
    
    try:
        import pygame
    except ImportError:
        logger.error("Cannot import pygame")
        return
    
    drivers_to_test = ['kmsdrm', 'fbdev', 'x11', 'wayland', 'directfb', 'dummy']
    
    for driver in drivers_to_test:
        logger.info(f"\nTesting driver: {driver}")
        os.environ['SDL_VIDEODRIVER'] = driver
        
        try:
            pygame.display.quit()
            pygame.display.init()
            
            # Try to get display info
            info = pygame.display.Info()
            logger.info(f"  ✓ Driver '{driver}' initialized")
            logger.info(f"    Display size: {info.current_w}x{info.current_h}")
            logger.info(f"    Hardware accelerated: {info.hw}")
            
            # Try to create a small test surface
            try:
                screen = pygame.display.set_mode((320, 240))
                logger.info(f"    ✓ Created test surface")
                pygame.display.quit()
            except Exception as e:
                logger.warning(f"    Could not create surface: {e}")
                
        except Exception as e:
            logger.error(f"  ✗ Driver '{driver}' failed: {e}")
    
    print()

def check_permissions():
    """Check file permissions"""
    logger.info("=== Checking Permissions ===")
    
    # Check DRM device permissions
    devices_to_check = [
        '/dev/dri/card0',
        '/dev/dri/card1',
        '/dev/dri/renderD128',
        '/dev/fb0',
        '/dev/fb1'
    ]
    
    for device in devices_to_check:
        if os.path.exists(device):
            try:
                stat_info = os.stat(device)
                mode = oct(stat_info.st_mode)[-3:]
                logger.info(f"{device}: mode={mode}, readable={os.access(device, os.R_OK)}, writable={os.access(device, os.W_OK)}")
            except Exception as e:
                logger.error(f"{device}: {e}")
    print()

def check_display_manager():
    """Check if any display manager is running"""
    logger.info("=== Display Manager Check ===")
    
    # Check for common display managers
    display_managers = ['lightdm', 'gdm3', 'sddm', 'xdm']
    for dm in display_managers:
        try:
            result = subprocess.run(['systemctl', 'is-active', dm], capture_output=True, text=True)
            if result.stdout.strip() == 'active':
                logger.warning(f"{dm} is running - this may interfere with framebuffer access")
        except:
            pass
    
    # Check for X11
    if os.environ.get('DISPLAY'):
        logger.warning("X11 DISPLAY variable is set - running in X11 environment")
    else:
        logger.info("No X11 DISPLAY set - good for framebuffer operation")
    print()

def suggest_fixes():
    """Suggest potential fixes based on diagnostics"""
    logger.info("=== Suggested Fixes ===")
    
    suggestions = []
    
    # Check if running as root or with proper groups
    if 'video' not in subprocess.run(['groups'], capture_output=True, text=True).stdout:
        suggestions.append("Add user to video group: sudo usermod -a -G video $USER")
    
    if 'render' not in subprocess.run(['groups'], capture_output=True, text=True).stdout:
        suggestions.append("Add user to render group: sudo usermod -a -G render $USER")
    
    # Check for framebuffer
    if not os.path.exists('/dev/fb0'):
        suggestions.append("No framebuffer found - check display cable and boot config")
        suggestions.append("Ensure dtoverlay=vc4-kms-v3d is in /boot/firmware/config.txt")
    
    # Check SDL packages
    try:
        subprocess.run(['sdl2-config', '--version'], capture_output=True, check=True)
    except:
        suggestions.append("Install SDL2 development files: sudo apt install libsdl2-dev")
    
    if suggestions:
        for suggestion in suggestions:
            logger.info(f"  • {suggestion}")
    else:
        logger.info("  No specific issues detected")
    print()

def main():
    """Run all diagnostics"""
    logger.info("RPIFrame Display Diagnostics")
    logger.info("=" * 40)
    print()
    
    check_environment()
    check_display_devices()
    check_sdl_info()
    check_permissions()
    check_display_manager()
    test_video_drivers()
    suggest_fixes()
    
    logger.info("Diagnostics complete!")

if __name__ == "__main__":
    main()