#!/usr/bin/env python3
"""
Create trendy montage for all clips in Media Pool.
Uses Whisper-WebUI for transcription and creates timeline with viral segments.
"""

import os
import sys
import logging

# Configure logging to see whisper_node logs
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Setup DaVinci Resolve API paths
RESOLVE_SCRIPT_API = os.environ.get("RESOLVE_SCRIPT_API", 
    r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
RESOLVE_SCRIPT_LIB = os.environ.get("RESOLVE_SCRIPT_LIB",
    r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll")

os.environ["RESOLVE_SCRIPT_API"] = RESOLVE_SCRIPT_API
os.environ["RESOLVE_SCRIPT_LIB"] = RESOLVE_SCRIPT_LIB

if sys.platform.startswith("win") and hasattr(os, "add_dll_directory"):
    resolve_dir = os.path.dirname(RESOLVE_SCRIPT_LIB)
    if os.path.exists(resolve_dir):
        os.add_dll_directory(resolve_dir)

modules_path = os.path.join(RESOLVE_SCRIPT_API, "Modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)

# Add project src to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import DaVinciResolveScript as dvr_script

import subprocess
import json
# from src.api.whisper_node import transcribe_with_whisper_node # Removed direct import
from src.api.viral_detector import find_viral_segments
from src.api.smart_editing import create_trendy_timeline

def transcribe_in_subprocess(file_path):
    """Run transcription in a separate process to avoid DLL conflicts with Resolve."""
    script_path = os.path.join(os.path.dirname(__file__), "transcribe_cli.py")
    if not os.path.exists(script_path):
        print(f"ERROR: CLI script not found at {script_path}")
        return {"error": "CLI script missing"}
        
    cmd = [sys.executable, script_path, file_path]
    
    # Create a STRICTLY CLEAN environment
    # Resolve injects many variables (PYTHONPATH, RESOLVE_*, QT_*, etc.) that can break other apps
    env = {}
    
    # Copy only essential variables
    keys_to_keep = ['SYSTEMROOT', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP', 'COMSPEC', 'PATH', 'USERNAME', 'USERPROFILE']
    for key in keys_to_keep:
        if key in os.environ:
            env[key] = os.environ[key]
            
    # Explicitly ensure our venv/Scripts is in PATH (it should be, but let's be safe)
    venv_scripts = os.path.dirname(sys.executable)
    if venv_scripts not in env.get('PATH', ''):
        env['PATH'] = venv_scripts + os.pathsep + env.get('PATH', '')
    
    print(f"  Running subprocess: {' '.join(cmd)}")
    try:
        # Run and capture output
        # encoding='utf-8' ensures we read Russian text correctly
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', check=False, env=env)
        
        # Print logs from stderr (for user visibility)
        if process.stderr:
            print(f"  [Subprocess Logs]:\n{process.stderr}")
            
        if process.returncode != 0:
            print(f"  ERROR: Subprocess exited with code {process.returncode}")
            return {"error": f"Subprocess failed with code {process.returncode}"}
            
        # Parse standard output
        output_json = process.stdout.strip()
        if not output_json:
            return {"error": "Empty output from subprocess"}
            
        return json.loads(output_json)
        
    except Exception as e:
        print(f"  ERROR running subprocess: {e}")
        return {"error": str(e)}

def get_all_clips(media_pool):
    """Get all clips from media pool recursively."""
    clips = []
    root_folder = media_pool.GetRootFolder()
    
    def process_folder(folder):
        folder_clips = folder.GetClipList()
        if folder_clips:
            clips.extend(folder_clips)
        for sub in folder.GetSubFolderList():
            process_folder(sub)
    
    process_folder(root_folder)
    return clips


def main():
    print("=" * 50)
    print("  Trendy Montage Creator")
    print("=" * 50)
    
    # Connect to Resolve
    resolve = dvr_script.scriptapp("Resolve")
    if not resolve:
        print("ERROR: Cannot connect to DaVinci Resolve")
        return 1
    
    print(f"Connected: {resolve.GetProductName()} {resolve.GetVersionString()}")
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()
    if not project:
        print("ERROR: No project open")
        return 1
    
    print(f"Project: {project.GetName()}")
    
    media_pool = project.GetMediaPool()
    clips = get_all_clips(media_pool)
    
    if not clips:
        print("ERROR: No clips in Media Pool")
        return 1
    
    print(f"\nFound {len(clips)} clips:")
    for c in clips:
        props = c.GetClipProperty()
        print(f"  - {c.GetName()} ({props.get('Duration', '?')})")
    
    # Process each video clip
    video_clips = []
    for c in clips:
        props = c.GetClipProperty()
        clip_type = props.get("Type", "")
        if "Video" in clip_type:
            video_clips.append(c)
    
    if not video_clips:
        print("ERROR: No video clips found")
        return 1
    
    print(f"\nProcessing {len(video_clips)} video clips...")
    
    for clip in video_clips:
        clip_name = clip.GetName()
        file_path = clip.GetClipProperty("File Path")
        
        print(f"\n{'='*40}")
        print(f"Processing: {clip_name}")
        print(f"Path: {file_path}")
        
        if not file_path or not os.path.exists(file_path):
            print(f"  SKIP: File not found at {file_path}")
            continue
        
        # Check for cache FIRST to avoid running subprocess if possible
        cache_path = file_path + ".whisper.json"
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            print(f"  Found cache: {cache_path}")
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    whisper_result = json.load(f)
                print("  Loaded transcription from cache.")
            except Exception as e:
                print(f"  ERROR loading cache: {e}")
                whisper_result = None
        else:
            # Transcribe
            print("  Transcribing with Whisper (Subprocess)...")
            whisper_result = transcribe_in_subprocess(file_path)
            
        if whisper_result is None:
            print("  ERROR: Transcription failed (returned None). Check logs above.")
            continue
        
        if "error" in whisper_result:
            print(f"  ERROR: {whisper_result['error']}")
            if "suggestions" in whisper_result:
                for s in whisper_result["suggestions"]:
                    print(f"    - {s}")
            continue
        
        text = whisper_result.get("text", "")
        segments = whisper_result.get("segments", [])
        print(f"  Transcription: {len(text)} chars, {len(segments)} segments")
        
        # Find viral segments
        print("  Finding viral moments...")
        viral_segments = find_viral_segments(whisper_result, max_segments=3)
        
        if not viral_segments:
            print("  No viral segments found, using full clip")
            # Use first 60 seconds as fallback
            edits = [{
                "clip_name": clip_name,
                "start_time": 0,
                "end_time": min(60, float(clip.GetClipProperty("Duration").split(":")[0])*3600 
                               + float(clip.GetClipProperty("Duration").split(":")[1])*60)
            }]
        else:
            print(f"  Found {len(viral_segments)} viral segments:")
            edits = []
            for i, seg in enumerate(viral_segments):
                print(f"    [{i+1}] {seg['start']:.1f}s - {seg['end']:.1f}s (score: {seg.get('total_score', 0):.1f})")
                edits.append({
                    "clip_name": clip_name,
                    "start_time": seg["start"],
                    "end_time": seg["end"]
                })
        
        # Create timeline
        timeline_name = f"Trendy_{clip_name.rsplit('.', 1)[0]}"
        print(f"  Creating timeline: {timeline_name}")
        
        result = create_trendy_timeline(resolve, edits, timeline_name)
        print(f"  Result: {result}")
    
    print("\n" + "=" * 50)
    print("  DONE!")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
