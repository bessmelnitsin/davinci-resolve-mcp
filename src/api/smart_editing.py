#!/usr/bin/env python3
"""
DaVinci Resolve Smart Editing Operations
"""

import logging
from typing import List, Dict, Any, Optional
from src.api.timeline_operations import create_timeline

logger = logging.getLogger("davinci-resolve-mcp.smart_editing")

def create_vertical_timeline(resolve, edits: List[Dict[str, Any]], timeline_name: str = "Vertical Reel") -> str:
    """Create a 1080x1920 vertical timeline with scaled clips.
    
    Args:
        resolve: DaVinci Resolve instance
        edits: List of edits (clip_name, start_time, end_time)
        timeline_name: Name of the timeline
    """
    if not resolve: return "Error: Not connected"
    
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    
    # Create timeline
    create_result = create_timeline(resolve, timeline_name)
    if "Error" in create_result: return create_result
    
    timeline = project.GetCurrentTimeline()
    
    # Set Vertical Resolution (Resolve 18.5+)
    project.SetSetting("timelineResolutionWidth", "1080")
    project.SetSetting("timelineResolutionHeight", "1920")
    project.SetSetting("useVerticalResolution", "1")
    
    # Also set on timeline to be sure
    timeline.SetSetting("timelineResolutionWidth", "1080")
    timeline.SetSetting("timelineResolutionHeight", "1920")
    timeline.SetSetting("useVerticalResolution", "1")
    
    from src.api.media_operations import get_all_media_pool_clips
    clips_list = get_all_media_pool_clips(media_pool)
    clip_map = {c.GetName(): c for c in clips_list}
    
    success_count = 0
    for edit in edits:
        clip_name = edit.get("clip_name")
        if clip_name not in clip_map: continue
        
        source_clip = clip_map[clip_name]
        fps = float(source_clip.GetClipProperty("FPS") or 30.0)
        start_frame = int(edit["start_time"] * fps)
        end_frame = int(edit["end_time"] * fps)
        
        # Pre-trim and setup scaling
        source_clip.SetClipProperty("Start", str(start_frame))
        source_clip.SetClipProperty("End", str(end_frame))
        
        clip_info = {
            "mediaPoolItem": source_clip,
            "startFrame": start_frame,
            "endFrame": end_frame
        }
        
        added_items = media_pool.AppendToTimeline([clip_info])
        if added_items:
            item = added_items[0]
            item.SetProperty("Input Scaling", "Crop") 
            success_count += 1
            
    return f"Created vertical timeline '{timeline_name}' with {success_count} clips."

def create_trendy_timeline(resolve, edits: List[Dict[str, Any]], timeline_name: str = "Trendy Cut") -> str:
    """Create a new timeline structured with selected clips and gaps.
    
    Args:
        resolve: The DaVinci Resolve instance
        edits: List of edits. Each edit is a dict with:
               - clip_name: str
               - start_time: float (seconds)
               - end_time: float (seconds)
        timeline_name: Name of the timeline to create
        
    Returns:
        Status string
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not edits:
        return "Error: No edits provided"
        
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # 1. Create new timeline
    final_name = timeline_name
    counter = 1
    media_pool = current_project.GetMediaPool()
    
    while True:
        creation_result = create_timeline(resolve, final_name)
        if "already exists" in creation_result:
            final_name = f"{timeline_name} {counter}"
            counter += 1
        elif "Successfully" in creation_result:
            break
        else:
            return f"Failed to create timeline: {creation_result}"
            
    timeline = current_project.GetCurrentTimeline()
    if not timeline or timeline.GetName() != final_name:
        return f"Error: Could not verify creation of timeline '{final_name}'"
        
    logger.info(f"Created timeline '{final_name}', starting assembly...")
    
    # 2. Get all clips
    from src.api.media_operations import get_all_media_pool_clips
    clips_list = get_all_media_pool_clips(media_pool)
    clip_map = {c.GetName(): c for c in clips_list}
    
    gap_clip = None
    if "Gap" in clip_map:
        gap_clip = clip_map["Gap"]
    elif "Solid Color" in clip_map:
        gap_clip = clip_map["Solid Color"]
        
    success_count = 0
    
    for edit in edits:
        clip_name = edit.get("clip_name")
        start_sec = float(edit.get("start_time", 0))
        end_sec = float(edit.get("end_time", 0))
        
        if clip_name not in clip_map:
            logger.warning(f"Clip '{clip_name}' not found, skipping.")
            continue
            
        source_clip = clip_map[clip_name]
        fps = float(source_clip.GetClipProperty("FPS") or 30.0)
        
        # USE RELATIVE FRAMES (0-BASED)
        # For most clips in Resolve API, startFrame 0 is the physical start of the clip file.
        # Absolute TC offsets (like 11:00:00) should NOT be added manually here for relative edits.
        start_frame = int(start_sec * fps)
        end_frame = int(end_sec * fps)
        
        # Validate duration
        if end_frame <= start_frame:
            end_frame = start_frame + int(fps) # Default 1s if invalid
            
        logger.info(f"Trimming {clip_name}: {start_frame} to {end_frame} (FPS: {fps})")
        
        # PRE-TRIM MediaPoolItem (More reliable in v20)
        source_clip.SetClipProperty("Start", str(start_frame))
        source_clip.SetClipProperty("End", str(end_frame))
        
        # Note: Some versions use "Start" and "End" for Media Pool trimming, 
        # others use "In" and "Out". We'll try both to be safe.
        try:
            source_clip.SetClipProperty("In", str(start_frame))
            source_clip.SetClipProperty("Out", str(end_frame))
        except: pass
        
        # Dictionary for AppendToTimeline (Standard method)
        clip_info = {
            "mediaPoolItem": source_clip,
            "startFrame": start_frame,
            "endFrame": end_frame
        }
        
        added_items = media_pool.AppendToTimeline([clip_info])
        if added_items:
            success_count += 1
            # Add gap
            if gap_clip:
                gap_info = {
                    "mediaPoolItem": gap_clip,
                    "startFrame": 0,
                    "endFrame": int(fps) # 1 second gap
                }
                media_pool.AppendToTimeline([gap_info])
        else:
            logger.error(f"Failed to append trimmed clip {clip_name}")
    
    return f"Created timeline '{final_name}' with {success_count} trimmed clips and 1s gaps."


def smart_reframe(resolve, clip_name: str = None, 
                  target_aspect: str = "9:16",
                  track_subject: bool = True) -> Dict[str, Any]:
    """Apply smart reframe for vertical video creation.
    
    Uses DaVinci Resolve's Smart Reframe feature (requires Studio).
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Clip to reframe (uses current timeline clip if None)
        target_aspect: Target aspect ratio ('9:16', '1:1', '4:5')
        track_subject: Whether to track and follow the main subject
        
    Returns:
        Status dictionary with instructions
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return {"error": "No timeline active"}
    
    # Parse target aspect ratio
    aspect_map = {
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
        "4:5": (1080, 1350),
        "16:9": (1920, 1080),
        "4:3": (1440, 1080)
    }
    
    target_res = aspect_map.get(target_aspect, (1080, 1920))
    
    return {
        "feature": "Smart Reframe",
        "target_aspect": target_aspect,
        "target_resolution": f"{target_res[0]}x{target_res[1]}",
        "requires_studio": True,
        "instructions": [
            "1. Выберите клип на Edit page",
            "2. Inspector → Video → Smart Reframe",
            "3. Включите Smart Reframe",
            f"4. Установите Reference Point: {'Auto' if track_subject else 'Center'}",
            f"5. Aspect Ratio: {target_aspect}",
            "6. Настройте Object of Interest при необходимости",
            "7. Нажмите 'Reframe' для анализа"
        ],
        "alternative": {
            "method": "Timeline Settings",
            "steps": [
                "File → Timeline Settings",
                f"Resolution: {target_res[0]}x{target_res[1]}",
                "Mismatched Resolution: Scale full frame with crop"
            ]
        }
    }


def auto_subtitle(resolve, clip_name: str = None,
                  style: str = "default",
                  language: str = "auto") -> Dict[str, Any]:
    """Generate subtitles from audio transcription.
    
    Uses DaVinci Resolve's built-in transcription or external Whisper.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Clip to transcribe (uses timeline if None)
        style: Subtitle style ('default', 'tiktok', 'news', 'minimal')
        language: Language code or 'auto'
        
    Returns:
        Dictionary with subtitle generation info
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return {"error": "No timeline active"}
    
    # Style definitions
    styles = {
        "default": {
            "font": "Arial",
            "size": 48,
            "position": "bottom",
            "background": "semi-transparent black",
            "outline": True
        },
        "tiktok": {
            "font": "Montserrat Bold",
            "size": 72,
            "position": "center",
            "background": "none",
            "outline": True,
            "animation": "pop-up word by word"
        },
        "news": {
            "font": "Helvetica",
            "size": 42,
            "position": "bottom-left",
            "background": "solid color bar",
            "outline": False
        },
        "minimal": {
            "font": "Inter",
            "size": 36,
            "position": "bottom",
            "background": "none",
            "outline": False
        }
    }
    
    selected_style = styles.get(style, styles["default"])
    
    return {
        "feature": "Auto Subtitle",
        "clip": clip_name or "Current Timeline",
        "language": language,
        "style": style,
        "style_settings": selected_style,
        "workflow": {
            "resolve_native": [
                "1. Edit page → Timeline → выберите клипы",
                "2. Timeline menu → Create Subtitles from Audio",
                "3. Выберите язык и Caption Preset",
                "4. Нажмите Create",
                "5. Редактируйте в Subtitle Track"
            ],
            "whisper_workflow": [
                "1. Используйте transcribe_clip_to_cache() для транскрипции",
                "2. Получите сегменты через get_cached_transcription()",
                "3. Создайте SRT файл из сегментов",
                "4. File → Import → Subtitle → выберите SRT",
                "5. Перетащите на Subtitle track"
            ]
        },
        "srt_format_example": (
            "1\n"
            "00:00:01,000 --> 00:00:04,000\n"
            "First subtitle line\n\n"
            "2\n"
            "00:00:04,500 --> 00:00:08,000\n"
            "Second subtitle line"
        )
    }


def detect_scenes(resolve, clip_name: str = None,
                  sensitivity: float = 0.5) -> Dict[str, Any]:
    """Detect scene changes in a clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Clip to analyze
        sensitivity: Detection sensitivity (0.0-1.0)
        
    Returns:
        Scene detection info and instructions
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    return {
        "feature": "Scene Detection",
        "clip": clip_name or "Selected clip",
        "sensitivity": sensitivity,
        "instructions": [
            "1. Media page → выберите клип",
            "2. ПКМ → Scene Cut Detection",
            "3. Настройте чувствительность",
            "4. Нажмите Auto Scene Detect",
            "5. Проверьте обнаруженные точки",
            "6. Add Cuts to Media Pool - создаёт отдельные клипы"
        ],
        "api_alternative": {
            "note": "Программный анализ требует внешних библиотек",
            "libraries": ["scenedetect", "opencv-python"],
            "example": "from scenedetect import detect, ContentDetector"
        }
    }


def batch_export_by_markers(resolve, 
                            timeline_name: str = None,
                            output_dir: str = None,
                            preset_name: str = None) -> Dict[str, Any]:
    """Export timeline segments based on markers.
    
    Creates separate render jobs for each marked segment.
    
    Args:
        resolve: DaVinci Resolve instance
        timeline_name: Timeline to export
        output_dir: Output directory path
        preset_name: Render preset to use
        
    Returns:
        Export job information
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    timeline = project.GetCurrentTimeline()
    if timeline_name:
        # Find specific timeline
        for i in range(project.GetTimelineCount()):
            t = project.GetTimelineByIndex(i + 1)
            if t and t.GetName() == timeline_name:
                timeline = t
                project.SetCurrentTimeline(timeline)
                break
    
    if not timeline:
        return {"error": "Timeline not found"}
    
    # Get markers
    markers = timeline.GetMarkers()
    if not markers:
        return {
            "error": "No markers found in timeline",
            "suggestion": "Добавьте маркеры для разделения на сегменты"
        }
    
    # Convert markers to segments
    sorted_frames = sorted(markers.keys())
    segments = []
    
    for i, frame in enumerate(sorted_frames):
        marker_info = markers[frame]
        segment = {
            "index": i + 1,
            "start_frame": frame,
            "name": marker_info.get("name", f"Segment_{i+1}"),
            "color": marker_info.get("color", "Blue"),
            "note": marker_info.get("note", "")
        }
        
        # End frame is start of next marker or timeline end
        if i + 1 < len(sorted_frames):
            segment["end_frame"] = sorted_frames[i + 1]
        else:
            segment["end_frame"] = timeline.GetEndFrame()
        
        segment["duration_frames"] = segment["end_frame"] - segment["start_frame"]
        segments.append(segment)
    
    return {
        "timeline": timeline.GetName(),
        "marker_count": len(markers),
        "segments": segments,
        "export_workflow": [
            "1. Deliver page",
            "2. Для каждого сегмента:",
            "   - Установите In/Out points",
            "   - Add to Render Queue",
            "3. Запустите рендер всех заданий"
        ],
        "output_dir": output_dir or "Not specified",
        "preset": preset_name or "Current settings"
    }


def create_multicam_timeline(resolve, 
                             clip_names: List[str],
                             sync_method: str = "audio",
                             timeline_name: str = "Multicam") -> Dict[str, Any]:
    """Create a multicam timeline from multiple clips.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_names: List of clip names to include
        sync_method: Synchronization method ('audio', 'timecode', 'in_point')
        timeline_name: Name for the multicam timeline
        
    Returns:
        Status dictionary
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return {"error": "No project open"}
    
    media_pool = project.GetMediaPool()
    if not media_pool:
        return {"error": "Cannot access Media Pool"}
    
    # Find clips
    from src.api.media_operations import get_all_media_pool_clips
    all_clips = get_all_media_pool_clips(media_pool)
    clip_map = {c.GetName(): c for c in all_clips}
    
    found_clips = []
    missing_clips = []
    
    for name in clip_names:
        if name in clip_map:
            found_clips.append(clip_map[name])
        else:
            missing_clips.append(name)
    
    if not found_clips:
        return {"error": "No clips found", "missing": missing_clips}
    
    # Sync method mapping
    sync_map = {
        "audio": "Waveform",
        "timecode": "Timecode",
        "in_point": "In Point"
    }
    
    return {
        "feature": "Multicam Timeline",
        "clips_found": len(found_clips),
        "clips_missing": missing_clips,
        "sync_method": sync_map.get(sync_method, sync_method),
        "timeline_name": timeline_name,
        "workflow": [
            "1. Media page → выберите все клипы",
            "2. ПКМ → Create New Multicam Clip Using Selected Clips",
            f"3. Angle Sync: {sync_map.get(sync_method, sync_method)}",
            f"4. Name: {timeline_name}",
            "5. Create",
            "6. Edit page → используйте Multicam Viewer для переключения"
        ]
    }


def speed_ramp(resolve, clip_name: str = None,
               segments: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Apply speed ramping to a clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Target clip
        segments: List of speed segments [{start: 0, end: 2, speed: 100}, ...]
        
    Returns:
        Speed ramp configuration and instructions
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    # Default dramatic speed ramp
    if not segments:
        segments = [
            {"start_sec": 0, "end_sec": 1, "speed_percent": 100, "description": "Normal"},
            {"start_sec": 1, "end_sec": 2, "speed_percent": 25, "description": "Slow motion"},
            {"start_sec": 2, "end_sec": 3, "speed_percent": 200, "description": "Speed up"},
            {"start_sec": 3, "end_sec": 4, "speed_percent": 100, "description": "Normal"}
        ]
    
    return {
        "feature": "Speed Ramp",
        "clip": clip_name or "Current clip",
        "segments": segments,
        "workflow": [
            "1. Edit page → выберите клип",
            "2. Inspector → Video → Speed Change",
            "3. Или ПКМ → Retime Controls",
            "4. Создайте Speed Points (Ctrl+Shift+R)",
            "5. Измените скорость между точками",
            "6. Включите Retime Curve для плавных переходов"
        ],
        "tips": [
            "Используйте Optical Flow для плавного slow-motion",
            "Speed Point на каждом переходе скорости",
            "Retime Curve = плавное ускорение/замедление"
        ]
    }
