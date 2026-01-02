#!/usr/bin/env python3
"""
Check the recent logs to see what's happening with the URL processing
"""

import os

def check_logs():
    """Read the last 50 lines of the log file."""
    log_file = "d:\\dev\\casestrainer\\logs\\casestrainer.log"
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            last_50 = lines[-50:]
            print("Last 50 lines of casestrainer.log:")
            print("=" * 50)
            for i, line in enumerate(last_50, 1):
                print(f"{i:2d}: {line.rstrip()}")
    except Exception as e:
        print(f"Error reading logs: {e}")

if __name__ == "__main__":
    check_logs()
