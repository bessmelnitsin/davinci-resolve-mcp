import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from .llm_client import LLMClient
from .viral_detector import ViralSegment, ViralConfig

logger = logging.getLogger("davinci-resolve-mcp.semantic_detector")

class SemanticDetector:
    """
    Uses Global LLM (OpenRouter/OpenAI) to analyze transcript content semantically.
    Finds viral clips based on humor, storytelling, and context, not just keywords.
    """
    
    def __init__(self):
        self.client = LLMClient()
        
    def analyze(self, 
                whisper_data: Dict[str, Any], 
                config: ViralConfig) -> List[ViralSegment]:
        """
        Analyze transcript with LLM.
        
        Args:
            whisper_data: Full Whisper JSON result
            config: Configuration for duration constraints
            
        Returns:
            List of ViralSegment objects
        """
        if not self.client.api_key or "PLACEHOLDER" in self.client.api_key:
            logger.warning("No valid API Key found. Skipping Semantic Analysis.")
            return []
            
        # Prepare context for LLM
        full_text = whisper_data.get("text", "")
        segments = whisper_data.get("segments", [])
        
        if len(segments) > 500:
            logger.warning("Transcript too long for single pass. Truncating to first 500 segments.")
            segments = segments[:500]
            
        # Create a time-coded transcript format for the LLM
        transcript_lines = []
        for i, seg in enumerate(segments):
            start = round(seg['start'], 1)
            end = round(seg['end'], 1)
            text = seg['text'].strip()
            transcript_lines.append(f"[{i}] {start}-{end}s: {text}")
            
        transcript_block = "\n".join(transcript_lines)
        
        system_prompt = (
            "You are an expert Video Editor for TikTok and Reels. "
            "Your goal is to find the most VIRAL, engaging, and coherent clips from a raw transcript."
        )
        
        user_prompt = f"""
        Analyze the following video transcript.
        Identify exactly {config.max_segments} clips that have the highest potential to go viral on TikTok/Reels.
        
        CONSTRAINTS:
        1. Each clip must be between {config.min_duration} and {config.max_duration} seconds.
        2. The clip must be a COMPLETE thought or story. Do not cut off sentences.
        3. Look for: specific jokes, surprising facts, intense emotional moments, or "truth bombs".
        4. IGNORE: boring intros, technical issues, silence, or mumbled parts.
        
        TRANSCRIPT:
        {transcript_block}
        
        OUTPUT FORMAT (JSON ONLY):
        Return a JSON object with a key "clips" containing a list of objects.
        Each object must have:
        - "start_index": int (index of the starting segment)
        - "end_index": int (index of the ending segment, inclusive)
        - "reason": str (marketing explanation why this is viral)
        - "score": int (0-100 viral potential)
        - "hook": str (the specific phrase that hooks the viewer)
        
        Example:
        {{
          "clips": [
            {{ "start_index": 12, "end_index": 18, "reason": "Funny punchline about cats", "score": 95, "hook": "You won't believe this" }}
          ]
        }}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            logger.info("Sending transcript to LLM for analysis...")
            response_text = self.client.chat_complete(messages, json_mode=True)
            
            if not response_text:
                return []
                
            # Parse JSON
            # Clean up potential markdown blocks
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            clips = data.get("clips", [])
            viral_segments = []
            
            for clip in clips:
                try:
                    start_idx = clip["start_index"]
                    end_idx = clip["end_index"]
                    
                    # Validate indices
                    if start_idx < 0 or end_idx >= len(segments) or start_idx > end_idx:
                        continue
                        
                    first_seg = segments[start_idx]
                    last_seg = segments[end_idx]
                    
                    # Extract full text for this range
                    text_parts = [s['text'].strip() for s in segments[start_idx : end_idx+1]]
                    full_clip_text = " ".join(text_parts)
                    
                    # Calculate real duration
                    start_time = first_seg['start']
                    end_time = last_seg['end']
                    duration = end_time - start_time
                    
                    # Build ViralSegment
                    v_seg = ViralSegment(
                        start=start_time,
                        end=end_time,
                        duration=duration,
                        text_preview=full_clip_text[:100] + "...",
                        full_text=full_clip_text,
                        total_score=clip.get("score", 80),
                        reason=f"[LLM] {clip.get('reason', 'High viral potential')}",
                        detected_hooks=[clip.get("hook", "")],
                        detected_emotions=["LLM-Selected"],
                        segment_indices=list(range(start_idx, end_idx+1))
                    )
                    viral_segments.append(v_seg)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse clip from LLM: {e}")
            
            logger.info(f"LLM found {len(viral_segments)} viral clips.")
            return viral_segments
            
        except Exception as e:
            logger.error(f"Semantic Analysis Failed: {e}")
            return []
