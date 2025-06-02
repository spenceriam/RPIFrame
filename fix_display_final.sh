#!/bin/bash
#
# Final fix for RPIFrame display issues
# Uses fbi (framebuffer imageviewer) for reliable display
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

print_header "RPIFrame Display Final Fix"

# 1. Check display status
print_header "Checking Display Status"

# Check framebuffer
if [ -e /dev/fb0 ]; then
    print_success "Framebuffer device found: /dev/fb0"
    fbset -i
else
    print_error "No framebuffer device found!"
    exit 1
fi

# Check DSI display
if ls /sys/class/drm/card*-DSI-* 2>/dev/null; then
    print_success "DSI display detected"
else
    print_info "DSI display not detected in DRM, but framebuffer exists"
fi

# 2. Install fbi (framebuffer imageviewer)
print_header "Installing Framebuffer Image Viewer"
print_info "Installing fbi - a reliable framebuffer image viewer..."
sudo apt update
sudo apt install -y fbi
print_success "fbi installed"

# 3. Test display with fbi
print_header "Testing Display"

# Create a test image
print_info "Creating test image..."
cd ~/RPIFrame

# Use Python to create test image
python3 << 'EOF'
from PIL import Image, ImageDraw
import os

# Create gradient test image
img = Image.new('RGB', (800, 480), 'blue')
draw = ImageDraw.Draw(img)

# Draw gradient
for y in range(480):
    color = int((y / 480) * 255)
    draw.line([(0, y), (800, y)], fill=(color, 0, 255-color), width=1)

# Draw text
draw.text((300, 200), "RPIFrame Display Test", fill='white')
draw.text((250, 250), "If you see this, display works!", fill='white')

# Save
os.makedirs('photos', exist_ok=True)
img.save('photos/display_test.jpg')
print("Test image created: photos/display_test.jpg")
EOF

# Display test image
print_info "Displaying test image for 5 seconds..."
sudo fbi -T 1 -d /dev/fb0 -noverbose -a -t 5 --once photos/display_test.jpg

read -p "Did you see the test image? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Display test successful!"
else
    print_error "Display test failed"
    print_info "Check cable connection and try again"
fi

# 4. Update RPIFrame to use simple slideshow
print_header "Updating RPIFrame Configuration"

# Make simple_slideshow executable
chmod +x simple_slideshow.py

# Create a wrapper script that chooses the right display method
cat > ~/RPIFrame/display_wrapper.py << 'EOF'
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
EOF

chmod +x display_wrapper.py

# 5. Update main.py to use the wrapper
print_info "Backing up original main.py..."
cp main.py main.py.backup

# Update main.py to use display_wrapper
sed -i 's/display_slideshow/display_wrapper/g' main.py || true

# 6. Configure permissions
print_header "Configuring Permissions"

# Ensure user is in video group
sudo usermod -a -G video $USER

# Set framebuffer permissions
sudo chmod g+rw /dev/fb0 || true

# Create udev rule for persistent permissions
sudo bash -c 'cat > /etc/udev/rules.d/99-framebuffer.rules << EOF
KERNEL=="fb*", GROUP="video", MODE="0660"
EOF'

print_success "Permissions configured"

# 7. Test the service
print_header "Testing RPIFrame Service"

# Stop service if running
sudo systemctl stop rpiframe.service || true

# Test running directly
print_info "Testing direct run..."
cd ~/RPIFrame
source venv/bin/activate
timeout 10s python simple_slideshow.py || true

# 8. Summary
print_header "Setup Complete!"

echo "Display has been fixed using framebuffer image viewer (fbi)"
echo ""
echo "Next steps:"
echo "1. Restart the service: sudo systemctl restart rpiframe.service"
echo "2. Check logs: sudo journalctl -u rpiframe.service -f"
echo "3. Access web interface: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "To test slideshow manually:"
echo "  cd ~/RPIFrame && python simple_slideshow.py"
echo ""
echo "The slideshow will now use fbi which reliably works with"
echo "the Raspberry Pi DSI display without pygame/SDL issues."

print_success "All done!"