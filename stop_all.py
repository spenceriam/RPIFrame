#!/usr/bin/env python3
"""
Stop all RPIFrame processes
"""

import subprocess
import sys
import os

def stop_all_processes():
    """Stop all RPIFrame related processes"""
    print("Stopping all RPIFrame processes...")
    
    # Process patterns to look for
    patterns = [
        'run.py',
        'main.py',
        'app.py',
        'display_slideshow.py',
        'simple_slideshow.py',
        'rpiframe'
    ]
    
    stopped = False
    
    for pattern in patterns:
        try:
            # Find processes
            result = subprocess.run(['pgrep', '-f', pattern], 
                                  capture_output=True, text=True)
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                own_pid = str(os.getpid())
                
                for pid in pids:
                    if pid and pid != own_pid:
                        try:
                            print(f"Stopping process {pid} ({pattern})")
                            subprocess.run(['kill', '-TERM', pid])
                            stopped = True
                        except Exception as e:
                            print(f"Error stopping process {pid}: {e}")
        except Exception as e:
            print(f"Error finding processes for {pattern}: {e}")
    
    # Also try systemctl if service exists
    try:
        result = subprocess.run(['systemctl', 'is-active', 'rpiframe.service'],
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print("Stopping rpiframe.service...")
            subprocess.run(['sudo', 'systemctl', 'stop', 'rpiframe.service'])
            stopped = True
    except:
        pass
    
    if stopped:
        print("✅ Processes stopped")
    else:
        print("No RPIFrame processes found")
    
    # Check if port 5000 is still in use
    try:
        result = subprocess.run(['lsof', '-i', ':5000'], 
                              capture_output=True, text=True)
        if result.stdout:
            print("\n⚠️  Port 5000 is still in use by:")
            print(result.stdout)
    except:
        pass

if __name__ == '__main__':
    stop_all_processes()