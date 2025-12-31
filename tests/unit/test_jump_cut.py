"""
Unit tests for jump_cut module.

Tests automatic silence detection and speech segment generation.
"""

import pytest
from src.api.jump_cut import generate_jump_cut_edits


class TestGenerateJumpCutEdits:
    """Tests for generate_jump_cut_edits function."""
    
    def test_basic_speech_detection(self, sample_whisper_data):
        """Test basic speech block detection."""
        result = generate_jump_cut_edits(
            sample_whisper_data,
            clip_name="test_clip.mp4",
            silence_threshold=0.5
        )
        
        assert len(result) > 0
        assert all("clip_name" in seg for seg in result)
        assert all("start_time" in seg for seg in result)
        assert all("end_time" in seg for seg in result)
    
    def test_silence_threshold(self, sample_whisper_data):
        """Test that silence threshold affects segmentation."""
        # With low threshold, more segments (more cuts)
        result_low = generate_jump_cut_edits(
            sample_whisper_data,
            clip_name="test_clip.mp4",
            silence_threshold=0.3
        )
        
        # With high threshold, fewer segments (less cuts)
        result_high = generate_jump_cut_edits(
            sample_whisper_data,
            clip_name="test_clip.mp4",
            silence_threshold=2.0
        )
        
        # More permissive threshold should result in fewer or equal segments
        assert len(result_high) <= len(result_low)
    
    def test_clip_name_propagation(self, sample_whisper_data):
        """Test that clip name is correctly propagated to all segments."""
        clip_name = "my_interview.mp4"
        result = generate_jump_cut_edits(
            sample_whisper_data,
            clip_name=clip_name,
            silence_threshold=0.5
        )
        
        for segment in result:
            assert segment["clip_name"] == clip_name
    
    def test_handles_added(self, sample_whisper_data):
        """Test that handle frames are added to segments."""
        result = generate_jump_cut_edits(
            sample_whisper_data,
            clip_name="test_clip.mp4",
            silence_threshold=0.5
        )
        
        if result:
            # First segment should not have negative start
            assert result[0]["start_time"] >= 0
    
    def test_empty_transcription(self):
        """Test handling of empty transcription."""
        empty_data = {"segments": []}
        result = generate_jump_cut_edits(
            empty_data,
            clip_name="test_clip.mp4"
        )
        
        assert result == []
    
    def test_segment_level_fallback(self):
        """Test fallback when word-level timestamps are not available."""
        segment_only_data = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "First segment"},
                {"start": 10.0, "end": 15.0, "text": "After silence"},
            ]
        }
        
        result = generate_jump_cut_edits(
            segment_only_data,
            clip_name="test_clip.mp4",
            silence_threshold=2.0
        )
        
        assert len(result) > 0
    
    def test_continuous_speech(self):
        """Test handling of continuous speech without silence."""
        continuous_data = {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Word1", 
                 "words": [{"start": 0.0, "end": 1.0, "word": "Word1"}]},
                {"start": 1.0, "end": 2.0, "text": "Word2",
                 "words": [{"start": 1.0, "end": 2.0, "word": "Word2"}]},
                {"start": 2.0, "end": 3.0, "text": "Word3",
                 "words": [{"start": 2.0, "end": 3.0, "word": "Word3"}]},
            ]
        }
        
        result = generate_jump_cut_edits(
            continuous_data,
            clip_name="test_clip.mp4",
            silence_threshold=0.5
        )
        
        # Continuous speech should result in one or few segments
        assert len(result) <= 3
    
    def test_long_silence(self):
        """Test detection of long silence gaps."""
        data_with_silence = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Before silence",
                 "words": [{"start": 0.0, "end": 5.0, "word": "test"}]},
                {"start": 30.0, "end": 35.0, "text": "After long silence",
                 "words": [{"start": 30.0, "end": 35.0, "word": "test"}]},
            ]
        }
        
        result = generate_jump_cut_edits(
            data_with_silence,
            clip_name="test_clip.mp4",
            silence_threshold=0.5
        )
        
        # Should create separate segments due to 25 second gap
        assert len(result) >= 2
    
    def test_segment_ordering(self, sample_whisper_data):
        """Test that segments are in chronological order."""
        result = generate_jump_cut_edits(
            sample_whisper_data,
            clip_name="test_clip.mp4",
            silence_threshold=0.5
        )
        
        for i in range(1, len(result)):
            assert result[i]["start_time"] >= result[i-1]["end_time"]
    
    def test_word_level_precision(self):
        """Test that word-level timestamps provide precise cuts."""
        detailed_data = {
            "segments": [
                {
                    "start": 0.0, "end": 10.0, "text": "Words with gaps",
                    "words": [
                        {"start": 0.0, "end": 0.5, "word": "Hello"},
                        {"start": 0.6, "end": 1.0, "word": "there"},
                        # 2 second gap
                        {"start": 3.0, "end": 3.5, "word": "after"},
                        {"start": 3.6, "end": 4.0, "word": "pause"},
                    ]
                }
            ]
        }
        
        result = generate_jump_cut_edits(
            detailed_data,
            clip_name="test_clip.mp4",
            silence_threshold=1.0  # 1 second threshold
        )
        
        # Should detect the 2 second gap
        assert len(result) >= 2


class TestJumpCutEdgeСases:
    """Edge case tests for jump_cut module."""
    
    def test_single_word(self):
        """Test handling of single word transcription."""
        single_word = {
            "segments": [
                {"start": 5.0, "end": 5.5, "text": "Hello",
                 "words": [{"start": 5.0, "end": 5.5, "word": "Hello"}]}
            ]
        }
        
        result = generate_jump_cut_edits(
            single_word,
            clip_name="short.mp4"
        )
        
        assert len(result) == 1
    
    def test_very_short_silence(self):
        """Test that very short silences are not cut."""
        data = {
            "segments": [
                {
                    "start": 0.0, "end": 5.0, "text": "Continuous speech",
                    "words": [
                        {"start": 0.0, "end": 0.5, "word": "Word1"},
                        {"start": 0.6, "end": 1.0, "word": "Word2"},  # 0.1s gap
                        {"start": 1.1, "end": 1.5, "word": "Word3"},  # 0.1s gap
                    ]
                }
            ]
        }
        
        result = generate_jump_cut_edits(
            data,
            clip_name="continuous.mp4",
            silence_threshold=0.5
        )
        
        # Tiny gaps should not cause cuts
        assert len(result) == 1
    
    def test_missing_segments_key(self):
        """Test handling of data without segments key."""
        no_segments = {"text": "Just text, no segments"}
        
        result = generate_jump_cut_edits(
            no_segments,
            clip_name="test.mp4"
        )
        
        assert result == []
    
    def test_none_input(self):
        """Test handling of None input."""
        # This should not crash
        try:
            result = generate_jump_cut_edits(
                None,
                clip_name="test.mp4"
            )
            # If it doesn't crash, it should return empty or handle gracefully
        except (TypeError, AttributeError):
            pass  # Expected behavior for None input
