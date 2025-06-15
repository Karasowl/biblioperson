#!/usr/bin/env python3
"""Wrapper script for deduplication CLI.

This script provides a convenient entry point for the deduplication CLI
that can be executed from anywhere in the project.

Usage:
    python dataset/scripts/dedup.py [command] [options]
    
Examples:
    python dataset/scripts/dedup.py list
    python dataset/scripts/dedup.py stats
    python dataset/scripts/dedup.py remove --hash abc123...
"""

import sys
from pathlib import Path

# Add the parent directory to the path for relative imports
SCRIPT_DIR = Path(__file__).resolve().parent
DATASET_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(DATASET_DIR.parent))

# Import and run the CLI
try:
    from dataset.processing.dedup_cli import main
    
    if __name__ == "__main__":
        sys.exit(main())
        
except ImportError as e:
    print(f"Error importing deduplication CLI: {e}")
    print("Make sure the deduplication system is properly installed.")
    sys.exit(1)
except Exception as e:
    print(f"Error running deduplication CLI: {e}")
    sys.exit(1) 