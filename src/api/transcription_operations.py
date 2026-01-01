"""
DaVinci Resolve Transcription Operations
"""

import os
import json
import logging
from typing import Dict, Any, List

from src.api.whisper_node import transcribe_with_whisper_node
from src.api.ai_director import prepare_transcription_for_ai
from src.api.media_operations import get_all_media_pool_clips

logger = logging.getLogger("davinci-resolve-mcp.transcription")

def transcribe_clip_to_cache(resolve, clip_name: str, model_size: str = "large-v3", force_retranscribe: bool = False) -> str:
    """Run Whisper transcription and save result to a .json file next to the media.
    
    Args:
        resolve: DaVinci Resolve object
        clip_name: Name of the clip to transcribe
        model_size: Whisper model size
        force_retranscribe: If True, ignore existing cache
    """
    if resolve is None: return "Error: Not connected"
    
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    file_path = target_clip.GetClipProperty("File Path")
    if not file_path: return "Error: File path not found"
    
    logger.info(f"Transcribing to cache: {clip_name}")
    whisper_data = transcribe_with_whisper_node(file_path, model_size=model_size, use_cache=not force_retranscribe)
    
    if "error" in whisper_data:
        return f"Transcription failed: {whisper_data['error']}"
        
    cache_path = file_path + ".whisper.json"
    return f"Success. Transcription cached at: {cache_path}"

def get_cached_transcription(resolve, clip_name: str) -> str:
    """Read transcription from cache without running Whisper.
    
    Args:
        resolve: DaVinci Resolve object
        clip_name: Name of the clip in Media Pool
    """
    if resolve is None: return "Error: Not connected"
    
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    file_path = target_clip.GetClipProperty("File Path")
    cache_path = file_path + ".whisper.json"
    
    if not os.path.exists(cache_path):
        return f"Error: No cache found at {cache_path}. Run 'transcribe_clip_to_cache' first."
        
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return prepare_transcription_for_ai(data)
    except Exception as e:
        return f"Error reading cache: {e}"

def get_clip_transcription(resolve, clip_name: str, model_size: str = "large-v3") -> str:
    """Helper that transcribes OR loads from cache and returns text.
    """
    if resolve is None: return "Error: Not connected"
    
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    file_path = target_clip.GetClipProperty("File Path")
    whisper_data = transcribe_with_whisper_node(file_path, model_size=model_size)
    
    if "error" in whisper_data: return f"Whisper failed: {whisper_data['error']}"
        
    return prepare_transcription_for_ai(whisper_data)

def get_all_media_pool_folders(media_pool):
    """Get all folders from media pool recursively."""
    folders = []
    root_folder = media_pool.GetRootFolder()
    
    def process_folder(folder):
        folders.append(folder)
        
        sub_folders = folder.GetSubFolderList()
        for sub_folder in sub_folders:
            process_folder(sub_folder)
    
    process_folder(root_folder)
    return folders

def clear_folder_transcription(resolve, folder_name: str) -> str:
    """Clear audio transcription for all clips in a folder.
    
    Args:
        resolve: DaVinci Resolve object
        folder_name: Name of the folder to clear transcriptions from
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the folder by name
    target_folder = None
    root_folder = media_pool.GetRootFolder()
    
    if folder_name.lower() == "root" or folder_name.lower() == "master":
        target_folder = root_folder
    else:
        # Search for the folder by name
        folders = get_all_media_pool_folders(media_pool)
        for folder in folders:
            if folder.GetName() == folder_name:
                target_folder = folder
                break
    
    if not target_folder:
        return f"Error: Folder '{folder_name}' not found in Media Pool"
    
    # Clear transcription for the folder
    try:
        result = target_folder.ClearTranscription()
        if result:
            return f"Successfully cleared audio transcription for folder '{folder_name}'"
        else:
            return f"Failed to clear audio transcription for folder '{folder_name}'"
    except Exception as e:
        return f"Error clearing audio transcription: {str(e)}"
