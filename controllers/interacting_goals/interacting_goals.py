"""Webots entry point for the SDK body adapter."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from goals.bridge import main

if __name__ == "__main__":
    main()
