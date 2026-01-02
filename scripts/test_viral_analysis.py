#!/usr/bin/env python3
"""
Test script for Viral Segment Detection
Opus Clip-like functionality for DaVinci Resolve MCP

This script demonstrates the viral segment detection workflow:
1. Connect to MCP server
2. Get clip from Media Pool
3. Transcribe with Whisper
4. Analyze for viral-worthy segments
5. Create timeline clips from best segments

Usage:
    python scripts/test_viral_analysis.py [clip_name]
"""

import asyncio
import os
import sys
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Paths
SERVER_SCRIPT = os.path.join(project_root, "src", "main.py")
VENV_PYTHON = os.path.join(project_root, "venv", "Scripts", "python.exe")

# Use system python if venv doesn't exist
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable


def setup_environment():
    """Setup Resolve environment variables for Windows."""
    env = os.environ.copy()
    
    if sys.platform.startswith("win"):
        resolve_script_api = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
        resolve_script_lib = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
        
        env["RESOLVE_SCRIPT_API"] = resolve_script_api
        env["RESOLVE_SCRIPT_LIB"] = resolve_script_lib
        
        python_path = env.get("PYTHONPATH", "")
        modules_path = os.path.join(resolve_script_api, "Modules")
        if modules_path not in python_path:
            env["PYTHONPATH"] = f"{python_path};{modules_path}" if python_path else modules_path
    
    return env


async def test_viral_analysis(clip_name: str = None):
    """
    Test the viral segment detection workflow.
    
    Args:
        clip_name: Optional clip name. If not provided, will list available clips.
    """
    print("=" * 60)
    print("VIRAL SEGMENT DETECTOR TEST")
    print("Opus Clip-like functionality for DaVinci Resolve")
    print("=" * 60)
    print()
    
    env = setup_environment()
    
    server_params = StdioServerParameters(
        command=VENV_PYTHON,
        args=[SERVER_SCRIPT],
        env=env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✓ Connected to DaVinci Resolve MCP Server")
                print()
                
                # List available tools
                tools = await session.list_tools()
                viral_tools = [t.name for t in tools.tools if "viral" in t.name.lower()]
                print(f"Available viral tools: {viral_tools}")
                print()
                
                # Step 1: Get available clips
                print("Step 1: Getting Media Pool clips...")
                clips_result = await session.read_resource("resolve://media-pool-clips")
                clips_text = clips_result.contents[0].text
                clips = json.loads(clips_text)
                
                valid_clips = [c for c in clips if isinstance(c, dict) and "name" in c]
                
                if not valid_clips:
                    print("No clips found in Media Pool!")
                    print("Please add video files with speech content to your project.")
                    return
                
                print(f"Found {len(valid_clips)} clips:")
                for i, c in enumerate(valid_clips[:10], 1):
                    print(f"  [{i}] {c['name']}")
                if len(valid_clips) > 10:
                    print(f"  ... and {len(valid_clips) - 10} more")
                print()
                
                # Select clip
                if not clip_name:
                    clip_name = valid_clips[0]['name']
                    print(f"Using first clip: {clip_name}")
                else:
                    if not any(c['name'] == clip_name for c in valid_clips):
                        print(f"Clip '{clip_name}' not found!")
                        return
                    print(f"Using specified clip: {clip_name}")
                print()
                
                # Step 2: Find viral segments
                print("Step 2: Analyzing for viral segments...")
                print("(This may take a moment for transcription)")
                print()
                
                result = await session.call_tool("find_viral_segments", arguments={
                    "clip_name": clip_name,
                    "content_style": "viral_reels",
                    "max_segments": 5,
                    "min_duration": 15.0,
                    "max_duration": 60.0
                })
                
                analysis_text = result.content[0].text
                print("Analysis Results:")
                print("-" * 40)
                print(analysis_text)
                print()
                
                # Step 3: Ask user if they want to create clips
                print("=" * 60)
                print("Would you like to create timeline clips from the best segments?")
                print("Run: create_viral_clips('" + clip_name + "') in the MCP server")
                print("=" * 60)
                
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


async def test_viral_detector_standalone():
    """
    Test the ViralSegmentDetector class directly without MCP.
    Useful for development and debugging.
    """
    print("Testing ViralSegmentDetector standalone...")
    print()
    
    # Import the detector
    from src.api.viral_detector import (
        ViralSegmentDetector, 
        ViralConfig, 
        ContentStyle,
        find_viral_segments,
        format_segments_for_display
    )
    
    # Sample whisper data for testing
    sample_whisper_data = {
        "language": "en",
        "text": "Here's the secret that nobody tells you about video editing. Most people think you need expensive software, but that's completely wrong. The truth is, the best editors focus on storytelling, not tools. Let me show you exactly what I mean. First, find your hook. Something that grabs attention immediately. Then, build tension. Make people want to know what happens next. Finally, deliver value. Give them something they didn't expect.",
        "segments": [
            {"start": 0.0, "end": 4.5, "text": "Here's the secret that nobody tells you about video editing."},
            {"start": 4.5, "end": 9.2, "text": "Most people think you need expensive software, but that's completely wrong."},
            {"start": 9.2, "end": 14.8, "text": "The truth is, the best editors focus on storytelling, not tools."},
            {"start": 14.8, "end": 18.5, "text": "Let me show you exactly what I mean."},
            {"start": 18.5, "end": 22.0, "text": "First, find your hook."},
            {"start": 22.0, "end": 25.5, "text": "Something that grabs attention immediately."},
            {"start": 25.5, "end": 28.0, "text": "Then, build tension."},
            {"start": 28.0, "end": 32.5, "text": "Make people want to know what happens next."},
            {"start": 32.5, "end": 35.0, "text": "Finally, deliver value."},
            {"start": 35.0, "end": 39.0, "text": "Give them something they didn't expect."},
        ]
    }
    
    # Test with default config
    print("Test 1: Default config (viral_reels)")
    print("-" * 40)
    segments = find_viral_segments(sample_whisper_data)
    print(format_segments_for_display(segments))
    print()
    
    # Test with custom config
    print("Test 2: Custom config (tutorial style, longer duration)")
    print("-" * 40)
    segments = find_viral_segments(
        sample_whisper_data,
        content_style="tutorial",
        min_duration=10.0,
        max_duration=45.0,
        max_segments=3
    )
    print(format_segments_for_display(segments))
    print()
    
    # Test Russian content
    sample_ru_data = {
        "language": "ru",
        "text": "Вот почему большинство людей не могут похудеть. Секрет в том, что диеты не работают! Да, вы не ослышались. Исследования показывают, что 95% диет проваливаются. Но есть один метод, который действительно работает.",
        "segments": [
            {"start": 0.0, "end": 4.0, "text": "Вот почему большинство людей не могут похудеть."},
            {"start": 4.0, "end": 8.5, "text": "Секрет в том, что диеты не работают!"},
            {"start": 8.5, "end": 11.0, "text": "Да, вы не ослышались."},
            {"start": 11.0, "end": 16.5, "text": "Исследования показывают, что 95% диет проваливаются."},
            {"start": 16.5, "end": 21.0, "text": "Но есть один метод, который действительно работает."},
        ]
    }
    
    print("Test 3: Russian content")
    print("-" * 40)
    segments = find_viral_segments(sample_ru_data, language="ru", min_duration=10.0)
    print(format_segments_for_display(segments))
    
    print()
    print("✓ Standalone tests completed!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test viral segment detection")
    parser.add_argument("clip_name", nargs="?", help="Name of clip in Media Pool")
    parser.add_argument("--standalone", action="store_true", 
                       help="Run standalone tests without DaVinci Resolve")
    
    args = parser.parse_args()
    
    if args.standalone:
        asyncio.run(test_viral_detector_standalone())
    else:
        asyncio.run(test_viral_analysis(args.clip_name))
