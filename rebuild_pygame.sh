#!/bin/bash
#
# Rebuild pygame with proper SDL2 support for Raspberry Pi DSI display
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_header "Pygame Rebuild Script for Raspberry Pi"

# 1. Install build dependencies
print_header "Installing Build Dependencies"
sudo apt update
sudo apt install -y \
    python3-dev \
    python3-setuptools \
    python3-pip \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libsdl2-gfx-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    libpng-dev \
    pkg-config

print_success "Build dependencies installed"

# 2. Activate virtual environment
print_header "Setting Up Environment"
cd ~/RPIFrame
source venv/bin/activate

# 3. Uninstall existing pygame
print_info "Uninstalling existing pygame..."
pip uninstall -y pygame || true

# 4. Clean pip cache
print_info "Cleaning pip cache..."
pip cache purge

# 5. Set build environment variables
print_header "Setting Build Environment"
export SDL_VIDEODRIVER=
export PYGAME_DETECT_AVX2=1

# 6. Build pygame from source
print_header "Building Pygame from Source"
print_info "This may take 10-15 minutes..."

# Try building with specific SDL config
SDL_CONFIG=$(which sdl2-config)
print_info "Using SDL config: $SDL_CONFIG"

# Install pygame with no binary, forcing compilation
pip install pygame --no-binary pygame --no-cache-dir -v

# 7. Test pygame installation
print_header "Testing Pygame Installation"

python << 'EOF'
import pygame
import sys

print(f"Pygame version: {pygame.ver}")
print(f"SDL version: {pygame.get_sdl_version()}")

pygame.init()

# List available drivers
drivers = []
for i in range(pygame.display.get_num_video_drivers()):
    drivers.append(pygame.display.get_video_driver(i))

print(f"Available video drivers: {drivers}")

# Try to init display with each driver
for driver in ['kmsdrm', 'fbdev', 'x11', 'wayland']:
    try:
        import os
        os.environ['SDL_VIDEODRIVER'] = driver
        pygame.display.quit()
        pygame.display.init()
        print(f"✓ Driver '{driver}' works!")
        pygame.display.quit()
    except:
        print(f"✗ Driver '{driver}' not available")
EOF

print_success "Pygame rebuild complete!"

# 8. Create test script
print_header "Creating Test Script"

cat > ~/RPIFrame/test_rebuilt_pygame.py << 'EOF'
#!/usr/bin/env python3
import os
import pygame
import sys

print("Testing rebuilt pygame...")

# Test different drivers
for driver in ['kmsdrm', 'fbdev']:
    print(f"\nTesting {driver} driver...")
    os.environ['SDL_VIDEODRIVER'] = driver
    
    try:
        pygame.init()
        pygame.display.init()
        
        # Try to create a display
        screen = pygame.display.set_mode((800, 480))
        print(f"✓ {driver} driver works! Created 800x480 display")
        
        # Draw something
        screen.fill((255, 0, 0))  # Red
        pygame.display.flip()
        
        # Wait a moment
        pygame.time.wait(1000)
        
        pygame.quit()
        break
        
    except Exception as e:
        print(f"✗ {driver} failed: {e}")
        pygame.quit()
EOF

chmod +x ~/RPIFrame/test_rebuilt_pygame.py

print_info "Run 'python ~/RPIFrame/test_rebuilt_pygame.py' to test the display"

print_header "Next Steps"
echo "1. Test the rebuilt pygame: python test_rebuilt_pygame.py"
echo "2. If display works, restart the service: sudo systemctl restart rpiframe.service"
echo "3. Check service logs: sudo journalctl -u rpiframe.service -f"

print_success "Script completed!"