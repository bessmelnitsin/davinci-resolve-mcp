#!/usr/bin/env python3
"""
Viral Segment Detector for DaVinci Resolve MCP

Advanced analysis of transcribed content to find viral-worthy segments.
Supports multiple languages (EN, RU) and content styles.

Features:
- Multi-factor scoring system
- Hook detection
- Emotional intensity analysis
- Pace and rhythm analysis
- Completeness detection
"""

import re
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger("davinci-resolve-mcp.viral_detector")


class ContentStyle(Enum):
    """Supported content styles for analysis."""
    VIRAL_REELS = "viral_reels"      # TikTok, Reels, Shorts (15-60s)
    HIGHLIGHT = "highlight"           # Key moments from long content
    TUTORIAL = "tutorial"             # Educational step-by-step
    PODCAST = "podcast"               # Podcast clips and quotes


@dataclass
class ViralConfig:
    """Configuration for viral segment detection."""
    min_duration: float = 15.0          # Minimum segment duration (seconds)
    max_duration: float = 60.0          # Maximum segment duration (seconds)
    target_duration: float = 30.0       # Ideal duration for scoring
    max_segments: int = 10              # Maximum number of segments to return
    content_style: ContentStyle = ContentStyle.VIRAL_REELS
    language: str = "auto"              # "en", "ru", or "auto"
    
    # Scoring weights (should sum to 100)
    hook_weight: int = 35          # Increased from 25
    emotion_weight: int = 15       # Decreased from 20
    completeness_weight: int = 25  # Increased from 20
    pace_weight: int = 15          # Same
    duration_weight: int = 10      # Decreased from 20


@dataclass
class ViralSegment:
    """A detected viral-worthy segment."""
    start: float                        # Start time in seconds
    end: float                          # End time in seconds
    duration: float                     # Duration in seconds
    text_preview: str                   # First 150 chars of text
    full_text: str                      # Complete segment text
    
    # Individual scores (0-100)
    hook_score: int = 0
    emotion_score: int = 0
    completeness_score: int = 0
    pace_score: int = 0
    duration_score: int = 0
    total_score: int = 0
    
    # Detected features
    detected_hooks: List[str] = field(default_factory=list)
    detected_emotions: List[str] = field(default_factory=list)
    reason: str = ""
    
    # Segment indices from whisper
    segment_indices: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ============================================================================
# Language-specific patterns and keywords
# ============================================================================

HOOK_PATTERNS = {
    "en": [
        (r"^here'?s?\s+(the|a|what|how|why)", "opener_heres"),
        (r"^(did you know|you won'?t believe)", "curiosity"),
        (r"^the\s+(secret|truth|problem|reason|key)\s+(is|to)", "revelation"),
        (r"^(stop|wait|listen|look|watch)\b", "attention_grab"),
        (r"^this\s+is\s+(why|how|what|the)", "statement"),
        (r"^(never|always|don'?t)\s+\w+\s+(this|that|these)", "warning"),
        (r"^(i|we)\s+(discovered|found|learned|realized)", "story"),
        (r"^(most|many)\s+people\s+(don'?t|think|believe)", "contrarian"),
        (r"^(the\s+)?number\s+one\s+(thing|reason|mistake)", "ranking"),
        (r"^\d+\s+(things?|ways?|tips?|hacks?|secrets?)", "listicle"),
    ],
    "ru": [
        (r"^(вот|и)\s+(почему|как|что|зачем|где)", "opener_vot"),
        (r"^(ты|вы)\s+(никогда|не)\s+(поверите|знали|догадаетесь)", "curiosity"),
        (r"^(секрет|правда|суть|фишка|проблема)\s+(в\s+том|заключается)", "revelation"),
        (r"^(стоп|погоди|подожди|слушай|смотри|зацени)\b", "attention_grab"),
        (r"^это\s+(самое|реально|просто)\s+(важное|жесть|крутое)", "statement"),
        (r"^(никогда|всегда|запомни|не)\s+(делай|говори|забывай)", "warning"),
        (r"^(короче|прикинь|представь|кстати)\b", "conversational_hook"),
        (r"^(я|мы)\s+(понял|узнал|офигел|решил)", "story"),
        (r"^(все|многие)\s+(думают|ошибаются|говорят)", "contrarian"),
        (r"^(топ|лучший|худший)\s+(способ|вариант|совет)", "ranking"),
        (r"^\d+\s+(вещей|причин|фактов|секретов)", "listicle"),
        (r"^(а)\s+(что|как)\s+(если|насчет)", "rhetorical"),
    ]
}

EMOTION_MARKERS = {
    "excitement": {
        "en": ["!", "wow", "amazing", "incredible", "insane", "awesome", "unbelievable", "mind-blowing"],
        "ru": ["!", "вау", "жесть", "ого", "супер", "класс", "офигеть", "круто", "шок", "бомба", "прикол"]
    },
    "question": {
        "en": ["?", "why", "how come", "what if", "have you ever", "do you know"],
        "ru": ["?", "почему", "зачем", "как так", "а что если", "знаешь", "видели"]
    },
    "surprise": {
        "en": ["wait", "hold on", "actually", "but here's the thing", "plot twist", "turns out"],
        "ru": ["стоп", "подожди", "на самом деле", "но вот", "оказывается", "внезапно", "прикинь"]
    },
    "urgency": {
        "en": ["now", "today", "immediately", "must", "need to", "don't miss", "before it's too late"],
        "ru": ["сейчас", "срочно", "надо", "быстрее", "прямо сейчас", "не пропусти"]
    },
    "authority": {
        "en": ["proven", "research shows", "scientists", "studies", "expert", "years of experience"],
        "ru": ["факт", "доказано", "эксперты", "опыт", "я уверен", "точно", "сто процентов"]
    },
    "slang": {
        "en": ["lol", "lmao", "cool", "fire"],
        "ru": ["кайф", "кринж", "олды", "имба", "треш", "жиза", "топчик"]
    }
}

WEAK_STARTS = {
    "en": ["so", "um", "uh", "like", "okay so", "and", "but", "well", "you know", "i mean"],
    "ru": ["ну", "ээ", "эм", "как бы", "типа", "в общем", "короче говоря", "значит", "слушай ну", "просто"]
}

SENTENCE_ENDINGS = {
    "en": [".", "!", "?", "...", "—"],
    "ru": [".", "!", "?", "...", "—", "…", ")"]
}


# ============================================================================
# Main Detector Class
# ============================================================================

class ViralSegmentDetector:
    """
    Multi-factor analyzer for finding viral-worthy video segments.
    
    Usage:
        detector = ViralSegmentDetector()
        segments = detector.analyze(whisper_data)
        
        # With custom config
        config = ViralConfig(max_duration=45, content_style=ContentStyle.TUTORIAL)
        segments = detector.analyze(whisper_data, config)
    """
    
    def __init__(self):
        self.config = ViralConfig()
    
    def analyze(self, 
                whisper_data: Dict[str, Any], 
                config: ViralConfig = None) -> List[ViralSegment]:
        """
        Analyze transcription and find viral-worthy segments.
        
        Args:
            whisper_data: Whisper transcription output with 'segments' key
            config: Optional configuration override
            
        Returns:
            List of ViralSegment objects sorted by total_score descending
        """
        if config:
            self.config = config
        
        segments = whisper_data.get("segments", [])
        if not segments:
            logger.warning("No segments found in whisper data")
            return []
        
        # Detect language if auto
        language = self._detect_language(whisper_data, segments)
        logger.info(f"Detected language: {language}")
        
        # Find candidate segment groups
        candidates = self._find_segment_groups(segments)
        logger.info(f"Found {len(candidates)} candidate segment groups")
        
        # Score each candidate
        viral_segments = []
        for candidate in candidates:
            scored = self._score_segment(candidate, language)
            if scored.total_score > 0:
                viral_segments.append(scored)
        
        # Sort by score and limit with overlap check
        viral_segments.sort(key=lambda x: x.total_score, reverse=True)
        
        final_segments = []
        for candidate in viral_segments:
            # Check overlap with already selected
            is_overlap = False
            for selected in final_segments:
                # Calculate IOE (Intersection Over Either) or just simple overlap
                overlap_start = max(candidate.start, selected.start)
                overlap_end = min(candidate.end, selected.end)
                overlap_duration = max(0, overlap_end - overlap_start)
                
                # If they overlap by more than 5 seconds (or 20% of duration), skip it
                if overlap_duration > 5.0:
                    is_overlap = True
                    break
            
            if not is_overlap:
                final_segments.append(candidate)
                if len(final_segments) >= self.config.max_segments:
                    break
        
        logger.info(f"Returning {len(final_segments)} viral segments (deduplicated)")
        return final_segments
    
    def _detect_language(self, whisper_data: Dict, segments: List[Dict]) -> str:
        """Detect language from whisper data or content analysis."""
        if self.config.language != "auto":
            return self.config.language
        
        # Try whisper's detected language
        whisper_lang = whisper_data.get("language", "")
        if whisper_lang in ["en", "english"]:
            return "en"
        if whisper_lang in ["ru", "russian"]:
            return "ru"
        
        # Simple heuristic: check for Cyrillic characters
        sample_text = " ".join(s.get("text", "") for s in segments[:5])
        cyrillic_count = len(re.findall(r'[а-яА-ЯёЁ]', sample_text))
        latin_count = len(re.findall(r'[a-zA-Z]', sample_text))
        
        if cyrillic_count > latin_count:
            return "ru"
        return "en"
    
    def _find_segment_groups(self, segments: List[Dict]) -> List[Dict]:
        """
        Group whisper segments into potential viral clips.
        
        Strategy:
        1. Start with each segment that could be a hook
        2. Extend until we hit max_duration or find a natural ending
        3. Ensure minimum duration
        """
        candidates = []
        used_indices = set()
        n = len(segments)
        
        for start_idx in range(n):
            if start_idx in used_indices:
                continue
            
            seg = segments[start_idx]
            group_segments = [seg]
            group_indices = [start_idx]
            current_duration = seg.get("end", 0) - seg.get("start", 0)
            combined_text = seg.get("text", "").strip()
            
            # Extend the group
            for j in range(start_idx + 1, n):
                next_seg = segments[j]
                next_duration = next_seg.get("end", 0) - next_seg.get("start", 0)
                
                # Check if adding this would exceed max duration
                potential_duration = current_duration + next_duration
                if potential_duration > self.config.max_duration:
                    break
                
                group_segments.append(next_seg)
                group_indices.append(j)
                current_duration = potential_duration
                combined_text += " " + next_seg.get("text", "").strip()
                
                # Check for natural ending point
                if self._is_natural_ending(combined_text) and current_duration >= self.config.min_duration:
                    break
            
            # Only add if meets minimum duration
            if current_duration >= self.config.min_duration:
                candidates.append({
                    "segments": group_segments,
                    "indices": group_indices,
                    "start": group_segments[0].get("start", 0),
                    "end": group_segments[-1].get("end", 0),
                    "duration": current_duration,
                    "text": combined_text.strip()
                })
                # Mark some indices as used to reduce overlap
                for idx in group_indices[:len(group_indices)//2]:
                    used_indices.add(idx)
        
        return candidates
    
    def _is_natural_ending(self, text: str) -> bool:
        """Check if text ends at a natural point (sentence end)."""
        text = text.strip()
        if not text:
            return False
        
        # Check for sentence-ending punctuation
        return text[-1] in ".!?…"
    
    def _score_segment(self, candidate: Dict, language: str) -> ViralSegment:
        """Calculate all scores for a candidate segment."""
        text = candidate["text"]
        duration = candidate["duration"]
        
        # Calculate individual scores
        hook_score, hooks = self._calculate_hook_score(text, language)
        emotion_score, emotions = self._calculate_emotion_score(text, language)
        completeness_score = self._calculate_completeness_score(text, language)
        pace_score = self._calculate_pace_score(candidate["segments"])
        duration_score = self._calculate_duration_score(duration)
        
        # Calculate weighted total
        total = (
            hook_score * self.config.hook_weight +
            emotion_score * self.config.emotion_weight +
            completeness_score * self.config.completeness_weight +
            pace_score * self.config.pace_weight +
            duration_score * self.config.duration_weight
        ) // 100
        
        # Generate reason
        reason = self._generate_reason(hook_score, emotion_score, completeness_score, hooks, emotions)
        
        return ViralSegment(
            start=candidate["start"],
            end=candidate["end"],
            duration=duration,
            text_preview=text[:150] + ("..." if len(text) > 150 else ""),
            full_text=text,
            hook_score=hook_score,
            emotion_score=emotion_score,
            completeness_score=completeness_score,
            pace_score=pace_score,
            duration_score=duration_score,
            total_score=total,
            detected_hooks=hooks,
            detected_emotions=emotions,
            reason=reason,
            segment_indices=candidate["indices"]
        )
    
    def _calculate_hook_score(self, text: str, language: str) -> Tuple[int, List[str]]:
        """
        Score based on opening hook quality.
        
        Returns:
            Tuple of (score 0-100, list of detected hook types)
        """
        score = 50  # Base score
        detected = []
        
        # Get first sentence for hook analysis
        first_sentence = text.split('.')[0].strip().lower()
        if not first_sentence:
            first_sentence = text[:100].lower()
        
        # Check for hook patterns
        patterns = HOOK_PATTERNS.get(language, HOOK_PATTERNS["en"])
        for pattern, hook_type in patterns:
            if re.search(pattern, first_sentence, re.IGNORECASE):
                score += 15
                detected.append(hook_type)
        
        # Penalty for weak starts
        weak_starts = WEAK_STARTS.get(language, WEAK_STARTS["en"])
        first_words = first_sentence.split()[:3]
        for weak in weak_starts:
            if any(weak in w for w in first_words):
                score -= 20
                break
        
        # Bonus for starting with a number (for listicles)
        if first_sentence and first_sentence[0].isdigit():
            score += 10
            detected.append("number_start")
        
        # Bonus for question start
        if text.strip()[:50].count('?') > 0:
            score += 10
            detected.append("question_start")
        
        return min(100, max(0, score)), detected
    
    def _calculate_emotion_score(self, text: str, language: str) -> Tuple[int, List[str]]:
        """
        Score based on emotional intensity.
        
        Returns:
            Tuple of (score 0-100, list of detected emotion types)
        """
        score = 40  # Base score
        detected = []
        text_lower = text.lower()
        
        for emotion_type, markers in EMOTION_MARKERS.items():
            lang_markers = markers.get(language, markers.get("en", []))
            for marker in lang_markers:
                if marker in text_lower:
                    score += 8
                    if emotion_type not in detected:
                        detected.append(emotion_type)
        
        # Bonus for exclamation marks (enthusiasm)
        exclaim_count = text.count('!')
        score += min(15, exclaim_count * 5)
        
        # Bonus for questions (engagement)
        question_count = text.count('?')
        score += min(10, question_count * 5)
        
        return min(100, max(0, score)), detected
    
    def _calculate_completeness_score(self, text: str, language: str) -> int:
        """
        Score based on whether the segment is a complete thought.
        
        Returns:
            Score 0-100
        """
        score = 50  # Base score
        text = text.strip()
        
        if not text:
            return 0
        
        # Check ending punctuation
        endings = SENTENCE_ENDINGS.get(language, SENTENCE_ENDINGS["en"])
        if text[-1] in endings:
            score += 20
        
        # Count complete sentences
        sentence_count = len(re.findall(r'[.!?]+', text))
        if sentence_count >= 2:
            score += 15
        if sentence_count >= 4:
            score += 10
        
        # Penalty if ends mid-word (truncated)
        if text[-1].isalpha() and not text.endswith(("...", "…")):
            score -= 20
        
        # Bonus for having intro + body structure
        if len(text) > 100 and sentence_count >= 2:
            score += 10
        
        return min(100, max(0, score))
    
    def _calculate_pace_score(self, segments: List[Dict]) -> int:
        """
        Score based on speech pace and rhythm.
        
        Looks for:
        - Consistent pace (not too many long pauses)
        - Natural rhythm
        - Appropriate word density
        
        Returns:
            Score 0-100
        """
        if not segments:
            return 50
        
        score = 60  # Base score
        
        # Calculate words per second
        total_words = sum(len(s.get("text", "").split()) for s in segments)
        total_duration = sum(s.get("end", 0) - s.get("start", 0) for s in segments)
        
        if total_duration > 0:
            wps = total_words / total_duration
            
            # Ideal WPS is around 2.5-3.5 for engaging content
            if 2.0 <= wps <= 4.0:
                score += 20
            elif 1.5 <= wps <= 4.5:
                score += 10
            elif wps < 1.0 or wps > 5.0:
                score -= 15
        
        # Check for long gaps between segments
        for i in range(1, len(segments)):
            gap = segments[i].get("start", 0) - segments[i-1].get("end", 0)
            if gap > 2.0:  # More than 2 second gap
                score -= 10
            elif gap > 1.0:
                score -= 5
        
        return min(100, max(0, score))
    
    def _calculate_duration_score(self, duration: float) -> int:
        """
        Score based on segment duration.
        
        Ideal duration varies by content style:
        - viral_reels: 15-45s (target 30s)
        - highlight: 30-90s (target 60s)
        - tutorial: 45-120s (target 90s)
        - podcast: 30-90s (target 45s)
        
        Returns:
            Score 0-100
        """
        target = self.config.target_duration
        min_dur = self.config.min_duration
        max_dur = self.config.max_duration
        
        # Perfect score at target duration
        if abs(duration - target) < 5:
            return 100
        
        # Linear decrease as we move away from target
        if duration < target:
            # Too short
            range_size = target - min_dur
            distance = target - duration
            if range_size > 0:
                return max(30, int(100 - (distance / range_size) * 70))
        else:
            # Too long
            range_size = max_dur - target
            distance = duration - target
            if range_size > 0:
                return max(30, int(100 - (distance / range_size) * 70))
        
        return 50
    
    def _generate_reason(self, 
                         hook_score: int, 
                         emotion_score: int, 
                         completeness_score: int,
                         hooks: List[str], 
                         emotions: List[str]) -> str:
        """Generate human-readable reason for the segment's score."""
        reasons = []
        
        if hook_score >= 70:
            hook_types = ", ".join(hooks[:2]) if hooks else "strong opening"
            reasons.append(f"Strong hook ({hook_types})")
        elif hook_score >= 50:
            reasons.append("Decent opening")
        else:
            reasons.append("Weak opening")
        
        if emotion_score >= 70:
            emotion_types = ", ".join(emotions[:2]) if emotions else "high energy"
            reasons.append(f"Emotionally engaging ({emotion_types})")
        elif emotion_score >= 50:
            reasons.append("Moderate engagement")
        
        if completeness_score >= 70:
            reasons.append("Complete thought")
        elif completeness_score < 40:
            reasons.append("May feel incomplete")
        
        return "; ".join(reasons)


# ============================================================================
# Helper Functions for MCP Integration
# ============================================================================

def find_viral_segments(whisper_data: Dict[str, Any],
                        content_style: str = "viral_reels",
                        max_segments: int = 5,
                        min_duration: float = 15.0,
                        max_duration: float = 60.0,
                        language: str = "auto") -> List[Dict[str, Any]]:
    """
    Wrapper function for MCP tool integration.
    
    Args:
        whisper_data: Whisper transcription output
        content_style: One of 'viral_reels', 'highlight', 'tutorial', 'podcast'
        max_segments: Maximum number of segments to return
        min_duration: Minimum segment duration in seconds
        max_duration: Maximum segment duration in seconds
        language: Language code ('en', 'ru', 'auto')
    
    Returns:
        List of viral segment dictionaries
    """
    try:
        style = ContentStyle(content_style)
    except ValueError:
        style = ContentStyle.VIRAL_REELS
    
    config = ViralConfig(
        min_duration=min_duration,
        max_duration=max_duration,
        max_segments=max_segments,
        content_style=style,
        language=language
    )
    
    detector = ViralSegmentDetector()
    segments = detector.analyze(whisper_data, config)
    
    return [seg.to_dict() for seg in segments]


def format_segments_for_display(segments: List[Dict[str, Any]]) -> str:
    """Format viral segments as human-readable string."""
    if not segments:
        return "No viral segments found."
    
    lines = [f"Found {len(segments)} viral segment(s):\n"]
    
    for i, seg in enumerate(segments, 1):
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        score = seg.get("total_score", 0)
        preview = seg.get("text_preview", "")
        reason = seg.get("reason", "")
        
        lines.append(f"[{i}] Score: {score}/100 | {start:.1f}s - {end:.1f}s ({end-start:.1f}s)")
        lines.append(f"    Reason: {reason}")
        lines.append(f"    Preview: \"{preview}\"")
        lines.append("")
    
    return "\n".join(lines)


def segments_to_edits(segments: List[Dict[str, Any]], 
                      clip_name: str) -> List[Dict[str, Any]]:
    """
    Convert viral segments to edit list format for timeline creation.
    
    Args:
        segments: List of viral segment dictionaries
        clip_name: Name of the source clip in Media Pool
        
    Returns:
        List of edit dictionaries compatible with create_trendy_timeline()
    """
    edits = []
    for seg in segments:
        edits.append({
            "clip_name": clip_name,
            "start_time": seg.get("start", 0),
            "end_time": seg.get("end", 0)
        })
    return edits
