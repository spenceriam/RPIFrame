#!/usr/bin/env python3
"""
RPIFrame - Main entry point
Run with: python3 run.py [options]
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the rpiframe module to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from rpiframe import PhotoFrame
except ImportError as e:
    print(f"Error importing RPIFrame: {e}")
    print("Please install dependencies: pip3 install -r requirements.txt")
    sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='RPIFrame - Digital Photo Frame for Raspberry Pi DSI Display',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run.py                    # Run full application
  python3 run.py --web-only         # Run only web interface
  python3 run.py --display-only     # Run only display slideshow
  python3 run.py --config custom.json # Use custom config file
        """
    )
    
    parser.add_argument(
        '--config', 
        default='config.json',
        help='Configuration file path (default: config.json)'
    )
    
    parser.add_argument(
        '--web-only', 
        action='store_true',
        help='Run only the web interface'
    )
    
    parser.add_argument(
        '--display-only', 
        action='store_true',
        help='Run only the display slideshow'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='RPIFrame 2.0.0'
    )
    
    args = parser.parse_args()
    
    # Setup basic logging before initializing PhotoFrame
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize PhotoFrame
        frame = PhotoFrame(args.config)
        
        # Start the application
        frame.start(
            web_only=args.web_only,
            display_only=args.display_only
        )
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()