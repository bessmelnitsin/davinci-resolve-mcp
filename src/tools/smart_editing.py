
"""
Smart Editing Tools for DaVinci Resolve MCP
Analysis, AI cuts, viral clips, etc.
"""
import os
import json
import logging
from typing import List, Dict, Any

from src.server_instance import mcp
from src.context import get_resolve
from src.api.whisper_node import transcribe_with_whisper_node
from src.api.jump_cut import generate_jump_cut_edits
from src.api.smart_editing import create_trendy_timeline as create_trendy_impl
from src.api.smart_editing import create_vertical_timeline
from src.api.viral_detector import (
    find_viral_segments as find_viral_segments_impl,
    format_segments_for_display
)

logger = logging.getLogger("davinci-resolve-mcp.smart_editing_tools")

@mcp.tool()
def smart_jump_cut(clip_name: str, silence_threshold: float = 0.5) -> str:
    """Automatically remove silence from a clip and create a new timeline.
    
    Args:
        clip_name: Name of the clip in Media Pool
        silence_threshold: Silence duration to cut (default 0.5s)
    """
    resolve = get_resolve()
    if resolve is None: return "Error: Not connected"
    
    from src.api.media_operations import get_all_media_pool_clips
    
    # Get project and media pool
    project_manager = resolve.GetProjectManager()
    if not project_manager: return "Error: No Project Manager"
    project = project_manager.GetCurrentProject()
    if not project: return "Error: No project open"
    
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    # Try to get absolute path from clip properties (Metalogging etc.)
    file_path = target_clip.GetClipProperty("File Path")
    
    if not file_path:
        return "Error: Could not determine file path of the clip for Whisper."
    
    # Node B: Transcribe
    logger.info(f"Transcribing {clip_name} with Whisper Node B...")
    whisper_data = transcribe_with_whisper_node(file_path)
    
    if "error" in whisper_data:
        return f"Whisper failed: {whisper_data['error']}"
        
    # Node C: Logic
    edits = generate_jump_cut_edits(whisper_data, clip_name, silence_threshold)
    
    # Node A: Assembly
    if not edits: return "No speech detected or entire clip is silence."
    
    result = create_trendy_impl(resolve, edits, f"JumpCut_{clip_name}")
    return result


@mcp.tool()
def viral_reels_factory(clip_name: str) -> str:
    """Generate 1080x1920 Reels from a source clip.
    
    Currently generates segments based on detected speech.
    """
    resolve = get_resolve()
    if resolve is None: return "Error: Not connected"
    
    from src.api.media_operations import get_all_media_pool_clips
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip: return f"Error: Clip '{clip_name}' not found"
    
    file_path = target_clip.GetClipProperty("File Path")
    whisper_data = transcribe_with_whisper_node(file_path)
    
    if "error" in whisper_data: return f"Whisper failed: {whisper_data['error']}"
    
    # Logic: Pick longer segments (3-8s) for 'viral' feel
    edits = generate_jump_cut_edits(whisper_data, clip_name, silence_threshold=2.0)
    
    # Assembly: Vertical
    result = create_vertical_timeline(resolve, edits, f"Reels_{clip_name}")
    return result


@mcp.tool()
def podcast_to_clips(
    clip_name: str,
    max_clips: int = 5,
    min_duration: float = 30.0,
    max_duration: float = 60.0,
    content_style: str = "podcast",
    create_timelines: bool = True
) -> str:
    """
    Convert a podcast episode into short viral clips (Opus Clip-like workflow).
    
    Complete one-click workflow that:
    1. Transcribes the podcast using Whisper
    2. Analyzes for best moments using AI scoring
    3. Creates separate timeline for each clip (optional)
    
    Args:
        clip_name: Podcast clip name in Media Pool
        max_clips: Maximum number of clips to create (default 5)
        min_duration: Minimum clip duration in seconds (default 30)
        max_duration: Maximum clip duration in seconds (default 60)
        content_style: Analysis style ('podcast', 'viral_reels', 'tutorial')
        create_timelines: Whether to create DaVinci timelines (default True)
    
    Returns:
        Summary of created clips with timestamps and scores
    
    Example:
        podcast_to_clips("My Podcast Episode.mp4", max_clips=3)
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    # Step 1: Get clip from media pool
    from src.api.media_operations import get_all_media_pool_clips
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    file_path = target_clip.GetClipProperty("File Path")
    if not file_path:
        return "Error: Could not determine file path"
    
    # Step 2: Transcribe
    logger.info(f"Step 1/3: Transcribing {clip_name}...")
    whisper_data = transcribe_with_whisper_node(file_path)
    
    if "error" in whisper_data:
        return f"Transcription failed: {whisper_data['error']}"
    
    # Step 3: Analyze for viral segments
    logger.info(f"Step 2/3: Analyzing for best moments...")
    segments = find_viral_segments_impl(
        whisper_data,
        content_style=content_style,
        max_segments=max_clips,
        min_duration=min_duration,
        max_duration=max_duration
    )
    
    if not segments:
        return "No suitable segments found. Try adjusting duration parameters."
    
    # Step 4: Create timelines (optional)
    results = []
    if create_timelines:
        logger.info(f"Step 3/3: Creating {len(segments)} timeline(s)...")
        for i, seg in enumerate(segments, 1):
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            score = seg.get("total_score", 0)
            preview = seg.get("text_preview", "")[:50]
            
            timeline_name = f"Clip_{i}_{clip_name}"
            edits = [{
                "clip_name": clip_name,
                "start_time": start,
                "end_time": end
            }]
            
            result = create_trendy_impl(resolve, edits, timeline_name)
            results.append({
                "clip": i,
                "timeline": timeline_name,
                "start": f"{start:.1f}s",
                "end": f"{end:.1f}s",
                "duration": f"{end-start:.1f}s",
                "score": score,
                "preview": preview,
                "status": "created" if "Timeline created" in result.lower() else result
            })
    else:
        for i, seg in enumerate(segments, 1):
            results.append({
                "clip": i,
                "start": f"{seg.get('start', 0):.1f}s",
                "end": f"{seg.get('end', 0):.1f}s",
                "duration": f"{seg.get('duration', 0):.1f}s",
                "score": seg.get("total_score", 0),
                "preview": seg.get("text_preview", "")[:80]
            })
    
    # Format output
    output_lines = [
        f"✅ Podcast to Clips Complete!",
        f"",
        f"Source: {clip_name}",
        f"Clips found: {len(segments)}",
        f"",
        "=" * 50
    ]
    
    for r in results:
        output_lines.append(f"[{r['clip']}] Score: {r['score']}/100 | {r.get('start', '')} - {r.get('end', '')} ({r.get('duration', '')})")
        if 'timeline' in r:
            output_lines.append(f"    Timeline: {r['timeline']}")
        output_lines.append(f"    Preview: \"{r['preview']}...\"")
        output_lines.append("")
    
    return "\n".join(output_lines)


@mcp.tool()
def analyze_content(
    file_path: str = None,
    clip_name: str = None,
    content_style: str = "viral_reels"
) -> str:
    """
    Analyze media content for viral potential without creating timelines.
    
    Provides detailed analysis with scoring breakdown. Use this to preview
    what segments would be selected before running full workflow.
    
    Args:
        file_path: Path to media file (use this OR clip_name)
        clip_name: Name of clip in Media Pool (use this OR file_path)
        content_style: Analysis style ('viral_reels', 'podcast', 'tutorial')
    
    Returns:
        Detailed analysis with segments and scores
    """
    resolve = get_resolve()
    
    # Get file path
    if clip_name and resolve:
        from src.api.media_operations import get_all_media_pool_clips
        project_manager = resolve.GetProjectManager()
        if project_manager:
            project = project_manager.GetCurrentProject()
            if project:
                media_pool = project.GetMediaPool()
                clips = get_all_media_pool_clips(media_pool)
                target_clip = next((c for c in clips if c.GetName() == clip_name), None)
                if target_clip:
                    file_path = target_clip.GetClipProperty("File Path")
    
    if not file_path:
        return "Error: Provide either file_path or clip_name (with DaVinci connected)"
    
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    
    # Transcribe
    whisper_data = transcribe_with_whisper_node(file_path)
    if "error" in whisper_data:
        return f"Transcription error: {whisper_data['error']}"
    
    # Analyze
    segments = find_viral_segments_impl(
        whisper_data,
        content_style=content_style,
        max_segments=10
    )
    
    if not segments:
        return "No segments found with viral potential."
    
    # Format detailed output
    output = {
        "file": os.path.basename(file_path),
        "language": whisper_data.get("language", "unknown"),
        "total_segments": len(segments),
        "analysis_style": content_style,
        "segments": []
    }
    
    for seg in segments:
        output["segments"].append({
            "start": round(seg.get("start", 0), 1),
            "end": round(seg.get("end", 0), 1),
            "duration": round(seg.get("duration", 0), 1),
            "scores": {
                "total": seg.get("total_score", 0),
                "hook": seg.get("hook_score", 0),
                "emotion": seg.get("emotion_score", 0),
                "completeness": seg.get("completeness_score", 0),
                "pace": seg.get("pace_score", 0),
                "duration": seg.get("duration_score", 0)
            },
            "reason": seg.get("reason", ""),
            "preview": seg.get("text_preview", "")
        })
    
    return json.dumps(output, ensure_ascii=False, indent=2)


@mcp.tool()
def find_viral_segments(clip_name: str, 
                        content_style: str = "viral_reels",
                        max_segments: int = 5,
                        min_duration: float = 15.0,
                        max_duration: float = 60.0,
                        language: str = "auto") -> str:
    """
    Analyze a clip and find the best viral-worthy moments using AI analysis.
    
    Uses multi-factor scoring:
    - Hook quality (opening strength)
    - Emotional intensity
    - Thought completeness
    - Speech pace and rhythm
    - Duration optimization
    
    Args:
        clip_name: Name of the clip in Media Pool
        content_style: Content type - 'viral_reels', 'highlight', 'tutorial', 'podcast'
        max_segments: Maximum number of segments to return (default 5)
        min_duration: Minimum segment duration in seconds (default 15)
        max_duration: Maximum segment duration in seconds (default 60)
        language: Language for analysis - 'en', 'ru', or 'auto' (default auto)
    
    Returns:
        Formatted string with found viral segments and their scores
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    # Get clip from media pool
    from src.api.media_operations import get_all_media_pool_clips
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    file_path = target_clip.GetClipProperty("File Path")
    if not file_path:
        return "Error: Could not determine file path for transcription"
    
    # Get or create transcription
    logger.info(f"Getting transcription for viral analysis: {clip_name}")
    whisper_data = transcribe_with_whisper_node(file_path)
    
    if "error" in whisper_data:
        return f"Transcription failed: {whisper_data['error']}"
    
    # Run viral segment detection
    logger.info(f"Running viral segment analysis with style: {content_style}")
    segments = find_viral_segments_impl(
        whisper_data,
        content_style=content_style,
        max_segments=max_segments,
        min_duration=min_duration,
        max_duration=max_duration,
        language=language
    )
    
    if not segments:
        return "No viral segments found. Try adjusting duration parameters or check if clip has speech content."
    
    # Format output
    output = format_segments_for_display(segments)
    output += f"\n\nTo create clips from these segments, use:\ncreate_viral_clips('{clip_name}')"
    
    return output


@mcp.tool()
def create_viral_clips(clip_name: str,
                       segments: List[Dict[str, Any]] = None,
                       auto_detect: bool = True,
                       content_style: str = "viral_reels",
                       max_segments: int = 3,
                       timeline_prefix: str = "Viral") -> str:
    """
    Create viral clips from a source video, either from provided segments or auto-detected.
    
    If segments are not provided and auto_detect is True, will automatically
    find the best viral moments using AI analysis.
    
    Args:
        clip_name: Name of the source clip in Media Pool
        segments: Optional list of segments with 'start' and 'end' times
        auto_detect: If True and no segments provided, auto-detect viral moments
        content_style: Style for auto-detection - 'viral_reels', 'highlight', etc.
        max_segments: Maximum segments for auto-detection (default 3)
        timeline_prefix: Prefix for created timeline names (default 'Viral')
    
    Returns:
        Status message with created timelines
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    from src.api.media_operations import get_all_media_pool_clips
    project = resolve.GetProjectManager().GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    media_pool = project.GetMediaPool()
    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    # Auto-detect segments if not provided
    if not segments and auto_detect:
        file_path = target_clip.GetClipProperty("File Path")
        if not file_path:
            return "Error: Could not determine file path for transcription"
        
        logger.info(f"Auto-detecting viral segments for: {clip_name}")
        whisper_data = transcribe_with_whisper_node(file_path)
        
        if "error" in whisper_data:
            return f"Transcription failed: {whisper_data['error']}"
        
        segments = find_viral_segments_impl(
            whisper_data,
            content_style=content_style,
            max_segments=max_segments
        )
        
        if not segments:
            return "No viral segments detected. Cannot create clips."
    
    if not segments:
        return "Error: No segments provided and auto_detect is False"
    
    # Create timelines for each segment
    results = []
    for i, seg in enumerate(segments, 1):
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        score = seg.get("total_score", 0)
        
        timeline_name = f"{timeline_prefix}_{i}_{clip_name}"
        edits = [{
            "clip_name": clip_name,
            "start_time": start,
            "end_time": end
        }]
        
        result = create_trendy_impl(resolve, edits, timeline_name)
        results.append(f"[{i}] {timeline_name} (score: {score}): {result}")
    
    return "\n".join([
        f"Created {len(results)} viral clip timeline(s):",
        ""
    ] + results)

