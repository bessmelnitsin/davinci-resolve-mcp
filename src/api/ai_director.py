#!/usr/bin/env python3
"""
AI Director Module for DaVinci Resolve MCP

Provides tools for AI-assisted video editing:
- Formatting transcriptions for LLM consumption
- Parsing AI-suggested edit points
- Generating edit decision lists (EDL)
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("davinci-resolve-mcp.ai_director")


def prepare_transcription_for_ai(whisper_data: dict, include_words: bool = False) -> str:
    """Format Whisper JSON for easier LLM reading.
    
    Args:
        whisper_data: Dictionary containing Whisper transcription output
        include_words: If True, include word-level timestamps
        
    Returns:
        A formatted string with numbered segments and timestamps
        
    Example output:
        [0] 0.00s - 5.20s: Hello and welcome to the video
        [1] 5.50s - 12.30s: Today we'll discuss Python programming
    """
    formatted_lines = []
    
    segments = whisper_data.get("segments", [])
    if not segments:
        # Try alternative structure
        if "text" in whisper_data:
            return f"[0] Full transcript: {whisper_data['text']}"
        return "No segments found in transcription"
    
    for i, segment in enumerate(segments):
        start = segment.get("start", 0)
        end = segment.get("end", 0)
        text = segment.get("text", "").strip()
        
        line = f"[{i}] {start:.2f}s - {end:.2f}s: {text}"
        formatted_lines.append(line)
        
        # Optionally include word-level detail
        if include_words and "words" in segment:
            for word_info in segment["words"]:
                w_start = word_info.get("start", 0)
                w_end = word_info.get("end", 0)
                word = word_info.get("word", word_info.get("text", ""))
                formatted_lines.append(f"    └─ {w_start:.2f}s-{w_end:.2f}s: {word}")
    
    return "\n".join(formatted_lines)


def parse_ai_segments(ai_selection_text: str, whisper_data: dict = None) -> List[Dict[str, Any]]:
    """Parse a list of segments suggested by AI.
    
    Supports multiple input formats:
    
    1. JSON format:
       [{"start": 12.5, "end": 45.0, "title": "Hook about coding"}]
       
    2. Text format (flexible):
       Reel 1: 12.5 - 45.0 (Hook about coding)
       Segment 2: 60.0-90.0 - The conclusion
       12.5 - 45.0: Some description
       
    3. Segment indices (requires whisper_data):
       Segments: 0, 3, 5-8, 12
       Use segments 0, 3, 5 through 8
       
    4. Timecode format:
       00:00:12.500 - 00:00:45.000
       
    Args:
        ai_selection_text: Text containing AI-suggested segments
        whisper_data: Optional Whisper transcription for index-based selection
        
    Returns:
        List of segment dictionaries with 'start', 'end', and optional 'title'
    """
    segments = []
    
    if not ai_selection_text or not ai_selection_text.strip():
        return segments
    
    # Method 1: Try JSON first
    try:
        # Handle both raw JSON and JSON embedded in text
        json_match = re.search(r'\[[\s\S]*\]', ai_selection_text)
        if json_match:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and ("start" in item or "end" in item):
                        segments.append({
                            "start": float(item.get("start", 0)),
                            "end": float(item.get("end", item.get("start", 0) + 10)),
                            "title": item.get("title", item.get("name", item.get("description", "")))
                        })
                if segments:
                    logger.info(f"Parsed {len(segments)} segments from JSON format")
                    return segments
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Method 2: Parse timecode format (HH:MM:SS.mmm or HH:MM:SS:FF)
    timecode_pattern = r'(\d{1,2}:\d{2}:\d{2}[.:]\d{2,3})\s*[-–]\s*(\d{1,2}:\d{2}:\d{2}[.:]\d{2,3})(?:\s*[-:]\s*(.+?))?(?:\n|$)'
    for match in re.finditer(timecode_pattern, ai_selection_text):
        start_tc = _parse_timecode(match.group(1))
        end_tc = _parse_timecode(match.group(2))
        title = match.group(3).strip() if match.group(3) else ""
        if start_tc is not None and end_tc is not None:
            segments.append({
                "start": start_tc,
                "end": end_tc,
                "title": title
            })
    
    if segments:
        logger.info(f"Parsed {len(segments)} segments from timecode format")
        return segments
    
    # Method 3: Parse text format (Reel N: start - end)
    # Patterns to try in order of specificity
    patterns = [
        # "Reel 1: 12.5 - 45.0 (Hook about coding)" or "Segment 2: 60-90 - Description"
        r'(?:Reel|Segment|Part|Clip|Cut)?\s*\d*\s*[:.]?\s*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)\s*(?:[-:(]\s*(.+?)\s*[):]?)?(?:\n|$)',
        # "12.5 - 45.0: Some description" or "12.5-45.0 (description)"  
        r'(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)\s*[:(-]\s*(.+?)(?:[)\n]|$)',
        # Simple "12.5 - 45.0" without description
        r'(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)(?:\s|$)',
    ]
    
    for pattern in patterns:
        matches = list(re.finditer(pattern, ai_selection_text, re.IGNORECASE))
        if matches:
            for i, match in enumerate(matches):
                start = float(match.group(1))
                end = float(match.group(2))
                title = match.group(3).strip() if len(match.groups()) >= 3 and match.group(3) else f"Segment {i+1}"
                
                # Validate
                if end > start:
                    segments.append({
                        "start": start,
                        "end": end,
                        "title": title
                    })
            if segments:
                logger.info(f"Parsed {len(segments)} segments from text format")
                return segments
    
    # Method 4: Parse segment indices (requires whisper_data)
    if whisper_data:
        whisper_segments = whisper_data.get("segments", [])
        if whisper_segments:
            # Look for patterns like "0, 3, 5-8" or "segments 1, 2, 3"
            index_pattern = r'(\d+)(?:\s*[-–]\s*(\d+))?'
            
            # First check if this looks like an index-based selection
            if re.search(r'(?:segment|use|include|select|#)\s*\d', ai_selection_text, re.IGNORECASE):
                for match in re.finditer(index_pattern, ai_selection_text):
                    start_idx = int(match.group(1))
                    end_idx = int(match.group(2)) if match.group(2) else start_idx
                    
                    for idx in range(start_idx, min(end_idx + 1, len(whisper_segments))):
                        seg = whisper_segments[idx]
                        segments.append({
                            "start": seg.get("start", 0),
                            "end": seg.get("end", 0),
                            "title": seg.get("text", "")[:50].strip()
                        })
                
                if segments:
                    logger.info(f"Parsed {len(segments)} segments from index format")
                    return segments
    
    logger.warning(f"Could not parse segments from: {ai_selection_text[:200]}...")
    return segments


def _parse_timecode(tc_string: str) -> Optional[float]:
    """Convert timecode string to seconds.
    
    Supports formats:
    - HH:MM:SS.mmm (milliseconds)
    - HH:MM:SS:FF (frames, assumes 24fps)
    - MM:SS.mmm
    - SS.mmm
    """
    try:
        # Normalize separator
        tc_string = tc_string.strip()
        
        # Handle different formats
        parts = re.split(r'[:.]', tc_string)
        
        if len(parts) == 4:
            # HH:MM:SS:FF or HH:MM:SS.mmm
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            
            # Check if last part is frames or milliseconds
            if int(parts[3]) < 100:
                # Likely frames (assuming 24fps)
                frames = int(parts[3])
                return hours * 3600 + minutes * 60 + seconds + frames / 24.0
            else:
                # Milliseconds
                milliseconds = int(parts[3])
                return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
                
        elif len(parts) == 3:
            # MM:SS.mmm or HH:MM:SS
            if '.' in tc_string:
                # MM:SS.mmm
                minutes = int(parts[0])
                seconds = int(parts[1])
                milliseconds = int(parts[2])
                return minutes * 60 + seconds + milliseconds / 1000.0
            else:
                # HH:MM:SS
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
                
        elif len(parts) == 2:
            # SS.mmm
            seconds = int(parts[0])
            milliseconds = int(parts[1])
            return seconds + milliseconds / 1000.0
            
        else:
            # Just seconds
            return float(tc_string)
            
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse timecode '{tc_string}': {e}")
        return None


def generate_edl_from_segments(segments: List[Dict[str, Any]], 
                                title: str = "AI_EDIT",
                                fps: float = 24.0) -> str:
    """Generate EDL (Edit Decision List) from segments.
    
    Args:
        segments: List of segment dictionaries with 'start', 'end', 'title'
        title: Title for the EDL
        fps: Frame rate for timecode conversion
        
    Returns:
        EDL content as string
    """
    edl_lines = [
        f"TITLE: {title}",
        f"FCM: NON-DROP FRAME",
        ""
    ]
    
    record_in = 0.0  # Timeline position
    
    for i, seg in enumerate(segments, 1):
        source_in = seg.get("start", 0)
        source_out = seg.get("end", source_in + 1)
        duration = source_out - source_in
        record_out = record_in + duration
        
        # Convert to timecode
        src_in_tc = _seconds_to_timecode(source_in, fps)
        src_out_tc = _seconds_to_timecode(source_out, fps)
        rec_in_tc = _seconds_to_timecode(record_in, fps)
        rec_out_tc = _seconds_to_timecode(record_out, fps)
        
        edl_lines.append(f"{i:03d}  AX       V     C        {src_in_tc} {src_out_tc} {rec_in_tc} {rec_out_tc}")
        
        title_text = seg.get("title", "")
        if title_text:
            edl_lines.append(f"* COMMENT: {title_text}")
        
        edl_lines.append("")
        record_in = record_out
    
    return "\n".join(edl_lines)


def _seconds_to_timecode(seconds: float, fps: float = 24.0) -> str:
    """Convert seconds to SMPTE timecode."""
    total_frames = int(seconds * fps)
    frames = total_frames % int(fps)
    total_seconds = total_frames // int(fps)
    secs = total_seconds % 60
    total_minutes = total_seconds // 60
    mins = total_minutes % 60
    hours = total_minutes // 60
    
    return f"{hours:02d}:{mins:02d}:{secs:02d}:{frames:02d}"


def suggest_viral_segments(whisper_data: dict, 
                           max_duration: float = 60.0,
                           min_duration: float = 15.0) -> List[Dict[str, Any]]:
    """Analyze transcription and suggest segments good for short-form content.
    
    Looks for:
    - Strong opening hooks
    - Complete thoughts/sentences
    - High-energy sections (detected by punctuation/keywords)
    
    Args:
        whisper_data: Whisper transcription data
        max_duration: Maximum segment duration in seconds
        min_duration: Minimum segment duration in seconds
        
    Returns:
        List of suggested segments with scores
    """
    segments = whisper_data.get("segments", [])
    if not segments:
        return []
    
    suggestions = []
    
    # Keywords that often indicate good content
    hook_keywords = [
        "secret", "hack", "tip", "trick", "never", "always", "must", "need",
        "important", "mistake", "wrong", "right", "best", "worst", "how to",
        "why", "what if", "imagine", "here's", "listen", "watch"
    ]
    
    current_group = []
    current_duration = 0.0
    
    for i, seg in enumerate(segments):
        seg_duration = seg.get("end", 0) - seg.get("start", 0)
        text = seg.get("text", "").lower()
        
        current_group.append(seg)
        current_duration += seg_duration
        
        # Check if we should end this group
        ends_sentence = any(text.rstrip().endswith(p) for p in ['.', '!', '?'])
        
        if current_duration >= min_duration and ends_sentence:
            if current_duration <= max_duration:
                # Score this segment group
                combined_text = " ".join(s.get("text", "") for s in current_group).lower()
                score = 0
                
                # Score based on hook keywords
                for keyword in hook_keywords:
                    if keyword in combined_text:
                        score += 10
                
                # Bonus for good length (30-45s is ideal for Reels)
                if 25 <= current_duration <= 50:
                    score += 20
                
                # Bonus for starting with hook word
                first_text = current_group[0].get("text", "").lower()
                if any(first_text.startswith(k) for k in ["so", "okay", "now", "but", "and"]):
                    score -= 5  # Penalty for weak starts
                if any(k in first_text for k in hook_keywords):
                    score += 15
                
                suggestions.append({
                    "start": current_group[0].get("start", 0),
                    "end": current_group[-1].get("end", 0),
                    "duration": current_duration,
                    "text_preview": combined_text[:100] + "...",
                    "score": score
                })
            
            # Reset for next group
            current_group = []
            current_duration = 0.0
    
    # Sort by score descending
    suggestions.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return suggestions[:10]  # Return top 10


def create_ai_prompt_for_editing(whisper_data: dict, style: str = "viral_reels") -> str:
    """Generate a prompt for AI to suggest edit points.
    
    Args:
        whisper_data: Whisper transcription data
        style: Type of content ('viral_reels', 'highlight', 'tutorial', 'podcast')
        
    Returns:
        Formatted prompt for LLM
    """
    transcript = prepare_transcription_for_ai(whisper_data)
    
    prompts = {
        "viral_reels": f"""Analyze this video transcript and suggest 3-5 segments perfect for Instagram/TikTok Reels (15-60 seconds each).

Look for:
- Strong hooks that grab attention
- Complete thoughts or stories
- Shareable moments or quotes
- High-energy or emotional peaks

Transcript:
{transcript}

Respond with JSON format:
[{{"start": 0.0, "end": 30.0, "title": "Hook about...", "reason": "Why this segment works"}}]""",

        "highlight": f"""Analyze this video transcript and identify the key highlights for a recap video.

Look for:
- Main points or conclusions
- Memorable quotes
- Important announcements
- Dramatic moments

Transcript:
{transcript}

Respond with JSON format:
[{{"start": 0.0, "end": 60.0, "title": "Topic name", "importance": "high/medium/low"}}]""",

        "tutorial": f"""Analyze this tutorial video transcript and identify distinct steps/sections.

Look for:
- Introduction and context
- Each step or instruction
- Tips and warnings
- Conclusion/summary

Transcript:
{transcript}

Respond with JSON format:
[{{"start": 0.0, "end": 45.0, "title": "Step 1: ...", "type": "intro/step/tip/conclusion"}}]""",

        "podcast": f"""Analyze this podcast transcript and suggest chapter markers.

Look for:
- Topic changes
- Key discussion points
- Guest introductions
- Q&A sections

Transcript:
{transcript}

Respond with JSON format:
[{{"start": 0.0, "end": 300.0, "title": "Chapter title", "summary": "Brief description"}}]"""
    }
    
    return prompts.get(style, prompts["viral_reels"])
