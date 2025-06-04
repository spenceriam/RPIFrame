#!/usr/bin/env python3
"""
Debug the exact image processing steps
"""
from PIL import Image, ImageOps
import glob

def debug_image_processing(image_path):
    print(f"\n=== DEBUG: {image_path} ===")
    
    # Load image
    pil_image = Image.open(image_path)
    print(f"1. Original loaded: {pil_image.size}")
    
    # Convert to RGB if needed
    if pil_image.mode not in ('RGB', 'RGBA'):
        pil_image = pil_image.convert('RGB')
        print(f"2. After RGB conversion: {pil_image.size}")
    else:
        print(f"2. Already RGB: {pil_image.size}")
    
    # Apply EXIF rotation
    pil_image = ImageOps.exif_transpose(pil_image)
    print(f"3. After EXIF rotation: {pil_image.size}")
    
    # Get dimensions for processing
    orig_width, orig_height = pil_image.size
    display_width, display_height = 800, 480
    
    img_ratio = orig_width / orig_height
    display_ratio = display_width / display_height
    
    print(f"4. Image ratio: {img_ratio:.3f} ({orig_width}/{orig_height})")
    print(f"5. Display ratio: {display_ratio:.3f} ({display_width}/{display_height})")
    
    # COVER MODE processing
    scale_for_width = display_width / orig_width
    scale_for_height = display_height / orig_height
    
    print(f"6. Scale for width: {scale_for_width:.6f}")
    print(f"7. Scale for height: {scale_for_height:.6f}")
    
    # Use LARGER scale factor
    scale_factor = max(scale_for_width, scale_for_height)
    print(f"8. Using scale factor: {scale_factor:.6f} ({'width' if scale_factor == scale_for_width else 'height'})")
    
    # Calculate new dimensions
    scaled_width = int(orig_width * scale_factor)
    scaled_height = int(orig_height * scale_factor)
    print(f"9. Scaled dimensions: {scaled_width}x{scaled_height}")
    
    # Resize the image
    pil_image = pil_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
    print(f"10. After resize: {pil_image.size}")
    
    # Determine crop
    if scaled_width > display_width:
        crop_left = (scaled_width - display_width) // 2
        crop_right = crop_left + display_width
        crop_top = 0
        crop_bottom = scaled_height
        print(f"11. HORIZONTAL CROP: ({crop_left}, {crop_top}, {crop_right}, {crop_bottom})")
        print(f"    Removing {scaled_width - display_width} pixels horizontally")
    else:
        crop_left = 0
        crop_right = scaled_width
        crop_top = (scaled_height - display_height) // 2
        crop_bottom = crop_top + display_height
        print(f"11. VERTICAL CROP: ({crop_left}, {crop_top}, {crop_right}, {crop_bottom})")
        print(f"    Removing {scaled_height - display_height} pixels vertically")
    
    # Apply crop
    pil_image = pil_image.crop((crop_left, crop_top, crop_right, crop_bottom))
    print(f"12. Final size after crop: {pil_image.size}")
    
    # Check final ratio
    final_ratio = pil_image.size[0] / pil_image.size[1]
    print(f"13. Final ratio: {final_ratio:.3f} (should be {display_ratio:.3f})")
    
    if abs(final_ratio - display_ratio) > 0.001:
        print(f"⚠️  RATIO MISMATCH! Expected {display_ratio:.3f}, got {final_ratio:.3f}")
    else:
        print(f"✅ Ratio is correct!")
    
    return pil_image

# Test with a few images
photo_dir = "/home/spencer/RPIFrame/photos"
images = glob.glob(f"{photo_dir}/*.jpg")[:3]  # Test first 3 images

for img_path in images:
    debug_image_processing(img_path)