#!/usr/bin/env python3
"""
Viral Detector — data classes for viral clip detection.

Used by ai_director.py and semantic_detector.py.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ViralConfig:
    """Configuration for viral clip detection."""
    min_duration: float = 15.0
    max_duration: float = 60.0
    max_segments: int = 5
    min_score: int = 50
    style: str = "viral_reels"


@dataclass
class ViralSegment:
    """A detected viral-worthy segment from a transcript."""
    start: float
    end: float
    duration: float
    text_preview: str = ""
    full_text: str = ""
    total_score: int = 0
    reason: str = ""
    detected_hooks: List[str] = field(default_factory=list)
    detected_emotions: List[str] = field(default_factory=list)
    segment_indices: List[int] = field(default_factory=list)
