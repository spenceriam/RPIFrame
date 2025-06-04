#!/usr/bin/env python3
"""
Debug photo paths and configuration
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rpiframe.config import Config

def debug_photos():
    """Debug photo configuration and paths"""
    print("=== RPIFrame Photo Debug ===\n")
    
    # Load config
    config = Config()
    
    # Show configuration
    print("Configuration:")
    print(f"  Photos directory: {config.photos.get('directory', 'photos')}")
    print(f"  Allowed extensions: {config.photos.get('allowed_extensions', [])}")
    print(f"  Max upload size: {config.photos.get('max_upload_size_mb', 50)}MB")
    
    # Check directories
    print("\nDirectory Status:")
    base_dir = Path(__file__).parent
    photos_dir = base_dir / config.photos.get('directory', 'photos')
    
    print(f"  Base directory: {base_dir}")
    print(f"  Photos directory: {photos_dir}")
    print(f"  Photos dir exists: {photos_dir.exists()}")
    
    if photos_dir.exists():
        # List photos
        photos = list(photos_dir.glob('*'))
        print(f"  Number of files: {len(photos)}")
        
        if photos:
            print("\n  Files found:")
            for photo in photos[:10]:  # Show first 10
                print(f"    - {photo.name}")
    
    # Check thumbnails
    thumbs_dir = photos_dir / "thumbnails"
    print(f"\n  Thumbnails dir: {thumbs_dir}")
    print(f"  Thumbnails dir exists: {thumbs_dir.exists()}")
    
    # Check old location
    old_photos = base_dir / "static" / "images" / "photos"
    if old_photos.exists():
        old_files = list(old_photos.glob('*'))
        if old_files:
            print(f"\n⚠️  Found {len(old_files)} files in old location: {old_photos}")
            print("  You may want to move these to the new location")
    
    # Create directories if missing
    if not photos_dir.exists():
        print("\n✅ Creating photos directory...")
        photos_dir.mkdir(parents=True, exist_ok=True)
        thumbs_dir.mkdir(exist_ok=True)
        print("  Directories created!")
    
    print("\n=== End Debug ===")

if __name__ == '__main__':
    debug_photos()