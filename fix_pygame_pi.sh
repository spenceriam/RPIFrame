#!/bin/bash
#
# Fix pygame for Raspberry Pi DSI display using system packages
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

print_header "Pygame Fix for Raspberry Pi"

# 1. Use system pygame which has proper Pi support
print_header "Installing System Pygame"
print_info "Installing Raspberry Pi optimized pygame..."
sudo apt update
sudo apt install -y python3-pygame

print_success "System pygame installed"

# 2. Link system pygame to virtual environment
print_header "Linking System Pygame to Virtual Environment"

# Find pygame location
PYGAME_PATH=$(python3 -c "import pygame; print(pygame.__file__)" 2>/dev/null | xargs dirname)
print_info "System pygame location: $PYGAME_PATH"

# Link to venv
cd ~/RPIFrame
source venv/bin/activate

# Remove any existing pygame in venv
pip uninstall -y pygame || true

# Create symlink
VENV_SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
if [ -d "$PYGAME_PATH" ]; then
    ln -sf $PYGAME_PATH $VENV_SITE_PACKAGES/
    print_success "Pygame linked to virtual environment"
else
    print_error "Could not find system pygame"
fi

# 3. Test pygame
print_header "Testing Pygame"

python << 'EOF'
import sys
try:
    import pygame
    print(f"✓ Pygame imported successfully")
    print(f"  Version: {pygame.ver}")
    print(f"  Location: {pygame.__file__}")
    
    # Initialize pygame
    pygame.init()
    
    # Check available drivers
    import os
    for driver in ['kmsdrm', 'fbdev', 'x11']:
        os.environ['SDL_VIDEODRIVER'] = driver
        try:
            pygame.display.quit()
            pygame.display.init()
            print(f"✓ Driver '{driver}' available")
            pygame.display.quit()
        except:
            print(f"✗ Driver '{driver}' not available")
            
except ImportError as e:
    print(f"✗ Failed to import pygame: {e}")
    sys.exit(1)
EOF

# 4. Create simple display test
print_header "Creating Display Test"

cat > ~/RPIFrame/quick_display_test.py << 'EOF'
#!/usr/bin/env python3
import os
import pygame
import sys
import time

print("Quick Display Test for DSI")
print("-" * 40)

# Try different drivers
drivers = ['kmsdrm', 'fbdev', 'x11']
working_driver = None

for driver in drivers:
    print(f"Trying {driver} driver...")
    os.environ['SDL_VIDEODRIVER'] = driver
    
    try:
        pygame.init()
        # Try to create a small test window
        screen = pygame.display.set_mode((800, 480))
        
        # If we got here, it worked!
        print(f"✓ SUCCESS: {driver} driver works!")
        working_driver = driver
        
        # Show a red screen for 2 seconds
        screen.fill((255, 0, 0))
        pygame.display.flip()
        time.sleep(2)
        
        pygame.quit()
        break
        
    except Exception as e:
        print(f"✗ {driver} failed: {e}")
        pygame.quit()

if working_driver:
    print(f"\n✓ Display test successful with {working_driver} driver!")
    print(f"Set SDL_VIDEODRIVER={working_driver} in your environment")
    
    # Update .env file
    with open('/home/spencer/RPIFrame/.env', 'w') as f:
        f.write(f"SDL_VIDEODRIVER={working_driver}\n")
        if working_driver == 'fbdev':
            f.write("SDL_FBDEV=/dev/fb0\n")
    print("Updated .env file with working driver")
else:
    print("\n✗ No working display driver found")
    print("Check your display connection and permissions")
EOF

chmod +x ~/RPIFrame/quick_display_test.py

# 5. Alternative: Use framebuffer directly
print_header "Alternative: Direct Framebuffer Access"

cat > ~/RPIFrame/test_framebuffer.py << 'EOF'
#!/usr/bin/env python3
import os
import struct
import mmap
import time

print("Direct Framebuffer Test")
print("-" * 40)

try:
    # Open framebuffer
    fb = open('/dev/fb0', 'r+b')
    
    # Get screen info
    import fcntl
    FBIOGET_VSCREENINFO = 0x4600
    FBIOGET_FSCREENINFO = 0x4602
    
    vinfo = fcntl.ioctl(fb, FBIOGET_VSCREENINFO, ' ' * 160)
    xres, yres, xres_v, yres_v, xoffset, yoffset, bits_per_pixel = struct.unpack('IIIIIII', vinfo[:28])
    
    print(f"Framebuffer info:")
    print(f"  Resolution: {xres}x{yres}")
    print(f"  Bits per pixel: {bits_per_pixel}")
    
    # Map framebuffer to memory
    screensize = xres * yres * (bits_per_pixel // 8)
    fbmem = mmap.mmap(fb.fileno(), screensize)
    
    # Fill screen with red (assuming 32-bit color)
    print("Filling screen with red...")
    for y in range(yres):
        for x in range(xres):
            offset = (y * xres + x) * 4
            fbmem[offset:offset+4] = struct.pack('BBBB', 0, 0, 255, 0)  # BGRA
    
    time.sleep(2)
    
    # Clear screen
    fbmem[:] = b'\x00' * screensize
    
    fbmem.close()
    fb.close()
    
    print("✓ Framebuffer test successful!")
    
except Exception as e:
    print(f"✗ Framebuffer test failed: {e}")
    print("Make sure you're in the 'video' group and /dev/fb0 exists")
EOF

chmod +x ~/RPIFrame/test_framebuffer.py

print_header "Next Steps"
echo "1. Test display: python ~/RPIFrame/quick_display_test.py"
echo "2. If that fails, try: python ~/RPIFrame/test_framebuffer.py"
echo "3. Once working, restart service: sudo systemctl restart rpiframe.service"
echo ""
echo "Note: You may need to logout/login for group changes to take effect"

print_success "Fix script completed!"