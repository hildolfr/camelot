#!/usr/bin/env python3
"""Clean up old timestamped log files after switching to rotating logs."""

import os
import glob

def cleanup_old_logs():
    """Remove old timestamped log files."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    
    # Find all old timestamped log files
    old_logs = glob.glob(os.path.join(log_dir, 'poker_game_*.log'))
    
    # Filter out the new rotating log files
    old_logs = [f for f in old_logs if not f.endswith('poker_game.log') 
                and not f.endswith('.1') and not f.endswith('.2') 
                and not f.endswith('.3') and not f.endswith('.4') 
                and not f.endswith('.5')]
    
    print(f"Found {len(old_logs)} old timestamped log files")
    
    if old_logs:
        response = input("Delete these files? (y/n): ")
        if response.lower() == 'y':
            for log_file in old_logs:
                try:
                    os.remove(log_file)
                    print(f"Removed: {os.path.basename(log_file)}")
                except Exception as e:
                    print(f"Error removing {log_file}: {e}")
            print(f"\nDeleted {len(old_logs)} old log files")
        else:
            print("Cleanup cancelled")
    else:
        print("No old log files to clean up")

if __name__ == "__main__":
    cleanup_old_logs()