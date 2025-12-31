#!/usr/bin/env python3
"""
DaVinci Resolve Audio Operations (Native AI Support)
"""

import logging
import os
import sys
import tempfile
import re
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger("davinci-resolve-mcp.audio")

def parse_srt(srt_path: str) -> List[Dict[str, Any]]:
    """Parse SRT file content into a list of segments with multi-encoding support."""
    segments = []
    content = ""
    # Try common encodings
    for encoding in ['utf-16', 'utf-8-sig', 'utf-8', 'cp1251', 'latin-1']:
        try:
            with open(srt_path, 'r', encoding=encoding) as f:
                content = f.read()
                if content and " --> " in content:
                    logger.info(f"Successfully read SRT with {encoding}")
                    break
        except Exception:
            continue
            
    if not content:
        logger.error(f"Failed to read SRT file {srt_path} with any supported encoding")
        return []
        
    # Standardize line endings and remove BOM
    content = content.replace('\ufeff', '').replace('\r\n', '\n')
    
    # DEBUG: Log first 200 chars to check format
    logger.info(f"SRT Content Preview (first 200 chars): {content[:200]}")
    
    try:
        # More robust regex for SRT blocks with potential extra spaces
        # Match: Index \n Time --> Time \n Text
        pattern = re.compile(r'(\d+)\s*\n(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*\n(.*?)(?=\n\n|\n\s*\n|$)', re.DOTALL)
        matches = pattern.findall(content)
        
        for match in matches:
            idx, start_str, end_str, text_block = match
            
            def time_to_sec(t_str):
                t_str = t_str.replace(',', '.')
                h, m, s_ms = t_str.split(':')
                return int(h) * 3600 + int(m) * 60 + float(s_ms)
                
            segments.append({
                "start": time_to_sec(start_str),
                "end": time_to_sec(end_str),
                "text": text_block.replace('\n', ' ').strip()
            })
            
    except Exception as e:
        logger.error(f"Error parsing SRT content: {e}")
        
    return segments

def transcribe_clip(resolve, clip_name: str, model_size: str = "auto") -> Dict[str, Any]:
    """Transcribe a clip using DaVinci Resolve's Native AI (Neural Engine).
    
    Args:
        resolve: The DaVinci Resolve instance
        clip_name: Name of the clip to transcribe
        model_size: Ignored for native AI (auto-selects)
        
    Returns:
        Dictionary containing transcription segments or error
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return {"error": "Failed to get Media Pool"}
        
    # Find the clip
    from src.api.media_operations import get_all_media_pool_clips
    all_clips = get_all_media_pool_clips(media_pool)
    
    target_clip = None
    for clip in all_clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
            
    if not target_clip:
        return {"error": f"Clip '{clip_name}' not found in Media Pool"}
        
    logger.info(f"Triggering native transcription for '{clip_name}'...")
    
    # Check if already transcribed
    props = target_clip.GetClipProperty()
    status = props.get("Transcription Status", "")
    logger.info(f"Clip '{clip_name}' transcription status: {status}")
    
    if status != "Transcribed":
        try:
            logger.info("Triggering native TranscribeAudio...")
            target_clip.TranscribeAudio("auto")
            
            # Wait for completion (status -> Transcribed)
            max_wait = 300 
            waited = 0
            while waited < max_wait:
                time.sleep(5)
                waited += 5
                new_props = target_clip.GetClipProperty()
                if new_props.get("Transcription Status") == "Transcribed":
                    logger.info("Transcription analysis finished by Resolve.")
                    break
                logger.debug(f"Still transcribing... ({waited}s / {max_wait}s)")
            
            if waited >= max_wait:
                logger.warning("Transcription timed out, attempting to proceed anyway.")
        except Exception as e:
            return {"error": f"TranscribeAudio error: {e}"}
            
    # Try to find text in properties/metadata directly (not standard but possible in some builds)
    for key in ["Transcription", "Transcription Text", "Audio Text"]:
        val = target_clip.GetMetadata(key)
        if val:
            logger.info(f"Found direct transcription in metadata key: {key}")
            # Mock segments if we only have one big text (better than nothing)
            return {"clip_name": clip_name, "text": val, "segments": [{"start": 0, "end": 10, "text": val}], "language": "auto"}
    
    # 2. Retrieve Text via Workaround
    # Since we can't get text directly, we create a temporary timeline,
    # generate subtitles (if necessary) or export the "transcription" as subtitles.
    # Actually, TranscribeAudio just adds metadata. 
    # Can we "Create Subtitles from Audio"? 
    # Yes, `timeline.CreateSubtitlesFromAudio()` is a thing in 18.5+.
    
    temp_timeline_name = f"Temp_Transcribe_{int(time.time())}"
    
    try:
        # Create temp timeline with the clip
        media_pool.CreateTimelineFromClips(temp_timeline_name, [target_clip])
        current_project.SetCurrentTimeline(current_project.GetTimelineByIndex(current_project.GetTimelineCount()))
        timeline = current_project.GetCurrentTimeline()
        
        # Create Subtitles from the transcription
        # Note: The API call might be `CreateSubtitlesFromAudio`.
        # Ensure the clip is in the timeline first.
        
        if hasattr(timeline, "CreateSubtitlesFromAudio"):
            logger.info("Creating subtitles from audio (asynchronous)...")
            timeline.CreateSubtitlesFromAudio()
            
            # Polling to wait for completion
            # On some systems, the dialog disappears when done, but we'll check if track has items
            max_wait = 300 # Up to 5 minutes for very long clips
            wait_step = 5
            total_waited = 0
            last_count = 0
            stable_checks = 0
            
            logger.info(f"Waiting for subtitle items to appear (max {max_wait}s)...")
            while total_waited < max_wait:
                items = timeline.GetItemListInTrack("subtitle", 1)
                current_count = len(items) if items else 0
                
                if current_count > 0:
                    if current_count == last_count:
                        stable_checks += 1
                    else:
                        stable_checks = 0 # Count is still growing
                        
                    if stable_checks >= 2: # Stable for 10 seconds
                        logger.info(f"Success! Found {current_count} subtitle items and count is stable.")
                        break
                    
                    logger.info(f"Found {current_count} items, waiting for stability...")
                
                last_count = current_count
                time.sleep(wait_step)
                total_waited += wait_step
                
            if total_waited >= max_wait:
                logger.warning("Timed out waiting for stable subtitle count. Proceeding with what we have.")
        else:
            logger.warning("timeline.CreateSubtitlesFromAudio not found. Transcription retrieval may fail.")
            
        # Export Subtitles to SRT
        temp_dir = tempfile.gettempdir()
        srt_path = os.path.join(temp_dir, f"{temp_timeline_name}.srt")
        
        # We'll try several common export types if standard fails
        # 1 = SRT in some versions/contexts
        export_types = [1] 
        if hasattr(resolve, "EXPORT_SUBTITLE"):
            export_types.insert(0, resolve.EXPORT_SUBTITLE)
            
        success_export = False
        for etype in export_types:
            logger.info(f"Attempting SRT export with type {etype}...")
            if timeline.Export(srt_path, etype):
                if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
                    success_export = True
                    break
        
        if not success_export:
             # Last ditch: try auto-detect with no second param if possible or EXPORT_NONE
             logger.info("Last ditch attempt at export with type 0...")
             timeline.Export(srt_path, 0)
             if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
                 success_export = True
        
        if success_export:
            logger.info(f"SRT Exported successfully. Size: {os.path.getsize(srt_path)} bytes")
        else:
            logger.error("All SRT export attempts failed.")
        
        # Parse SRT
        segments = []
        if os.path.exists(srt_path):
            segments = parse_srt(srt_path)
            
        # Fallback: Extraction from TimelineItems if SRT failed or returned no segments
        if not segments:
            logger.info("SRT parsing provided no segments. Attempting direct extraction from TimelineItems...")
            items = timeline.GetItemListInTrack("subtitle", 1)
            if items:
                v_items = timeline.GetItemListInTrack("video", 1)
                clip_start_in_timeline = v_items[0].GetStart() if v_items else 0
                logger.info(f"Video clip starts at frame {clip_start_in_timeline} in temp timeline.")
                
                fps = float(target_clip.GetClipProperty("FPS") or 30.0)
                for item in items:
                    # GetStart/GetDuration return frames in timeline context
                    # To get relative time to clip, we subtract clip_start_in_timeline
                    start_frame = item.GetStart()
                    duration = item.GetDuration()
                    
                    segments.append({
                        "start": (start_frame - clip_start_in_timeline) / fps,
                        "end": (start_frame + duration - clip_start_in_timeline) / fps,
                        "text": item.GetName() or f"Speech Segment {len(segments)+1}"
                    })
                logger.info(f"Direct extraction successful. Found {len(segments)} segments relative to clip start.")
        
        full_text = " ".join([s["text"] for s in segments])
        
        # Save TXT for IntelliScript
        try:
            trans_dir = os.path.join(os.getcwd(), "transcriptions")
            if not os.path.exists(trans_dir): os.makedirs(trans_dir)
            txt_path = os.path.join(trans_dir, f"{clip_name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            logger.info(f"Transcription exported to: {txt_path}")
        except Exception as te:
            logger.warning(f"Failed to export TXT: {te}")
            
        # Add markers to the clip for visibility in Media Pool
        # Note: items on track 1 of a 1-clip timeline should match clip times
        try:
            for seg in segments[:20]: # Only first 20 to avoid clutter
                target_clip.AddMarker(seg["start"] * fps, "Blue", f"Trans: {seg['text'][:20]}", "", 1)
        except: pass

        # Cleanup
        try:
            if os.path.exists(srt_path): os.remove(srt_path)
        except: pass
        
        media_pool.DeleteTimelines([timeline])
        
        if segments:
            return {
                "clip_name": clip_name,
                "text": full_text,
                "segments": segments,
                "language": "auto",
                "txt_path": txt_path if 'txt_path' in locals() else None
            }
        else:
            return {"error": "Failed to extract any transcription segments from timeline or SRT."}

    except Exception as e:
        # Try cleanup
        try:
             media_pool.DeleteTimelines([timeline])
        except:
            pass
        return {"error": f"Native text retrieval failed: {e}"}

def transcribe_folder(resolve, folder_name: str) -> Dict[str, Any]:
    """Transcribe all clips in a specific media pool folder.
    
    Args:
        resolve: The DaVinci Resolve instance
        folder_name: Name of the folder to transcribe
        
    Returns:
        Summary of transcription results
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    media_pool = current_project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    
    target_folder = None
    if folder_name.lower() in ["master", root_folder.GetName().lower()]:
        target_folder = root_folder
    else:
        # Search for folder
        def find_folder(parent, name):
            if parent.GetName() == name:
                return parent
            for sub in parent.GetSubFolderList():
                found = find_folder(sub, name)
                if found: return found
            return None
        target_folder = find_folder(root_folder, folder_name)
        
    if not target_folder:
        return {"error": f"Folder '{folder_name}' not found."}
        
    clips = target_folder.GetClipList()
    if not clips:
        return {"info": f"No clips in folder '{folder_name}'."}
        
    success_count = 0
    errors = []
    
    for clip in clips:
        try:
            if clip.TranscribeAudio("auto"):
                success_count += 1
            else:
                errors.append(f"Failed to transcribe {clip.GetName()}")
        except Exception as e:
            errors.append(f"Error in {clip.GetName()}: {str(e)}")
            
    return {
        "folder": folder_name,
        "total_clips": len(clips),
        "transcribed_count": success_count,
        "errors": errors
    }
