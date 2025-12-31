
import logging
from typing import List, Dict, Any

logger = logging.getLogger("davinci-resolve-mcp.jump_cut")

def generate_jump_cut_edits(whisper_data: dict, clip_name: str, silence_threshold: float = 0.5) -> List[dict]:
    """Analyze Whisper JSON (Word Level) and return list of segments with speech.
    
    Args:
        whisper_data: JSON from Whisper with word timestamps.
        clip_name: Name of the source clip in Media Pool.
        silence_threshold: Gap in seconds to be considered "silence" to cut.
        
    Returns:
        List of edits: [{"clip_name": ..., "start_time": ..., "end_time": ...}, ...]
    """
    all_words = []
    for segment in whisper_data.get("segments", []):
        if "words" in segment:
            all_words.extend(segment["words"])
        else:
            # Fallback to segment level if no words
            all_words.append({
                "start": segment["start"],
                "end": segment["end"]
            })
            
    if not all_words:
        return []
        
    # Sort just in case
    all_words.sort(key=lambda x: x["start"])
    
    speech_blocks = []
    if not all_words:
        return []
        
    current_block_start = all_words[0]["start"]
    current_block_end = all_words[0]["end"]
    
    for i in range(1, len(all_words)):
        word = all_words[i]
        gap = word["start"] - current_block_end
        
        if gap > silence_threshold:
            # Silence detected, end current block and start new one
            speech_blocks.append({
                "clip_name": clip_name,
                "start_time": max(0, current_block_start - 0.1), # Add handle
                "end_time": current_block_end + 0.1             # Add handle
            })
            current_block_start = word["start"]
        
        current_block_end = word["end"]
        
    # Add last block
    speech_blocks.append({
        "clip_name": clip_name,
        "start_time": max(0, current_block_start - 0.1),
        "end_time": current_block_end + 0.1
    })
    
    logger.info(f"Jump Cut: Reduced clip to {len(speech_blocks)} speech segments.")
    return speech_blocks
