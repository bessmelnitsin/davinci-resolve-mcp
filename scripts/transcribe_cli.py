#!/usr/bin/env python3
"""
CLI entry point for Whisper transcription.
Used to run transcription in a separate process to avoid GIL/DLL conflicts with DaVinci Resolve.
"""
import sys
import os
import json
import logging

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.api.whisper_node import transcribe_with_whisper_node

# Configure logging to stderr so stdout stays clean for JSON output
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s: %(message)s')

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python transcribe_cli.py <file_path>"}), file=sys.stdout)
        return 1
    
    file_path = sys.argv[1]
    
    # Run transcription
    # Note: logs will go to stderr
    result = transcribe_with_whisper_node(file_path)
    
    # Output only the JSON result to stdout, ensuring UTF-8
    if result:
        # Force stdout to utf-8
        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False), file=sys.stdout)
    else:
        print(json.dumps({"error": "Transcription returned None"}), file=sys.stdout)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
