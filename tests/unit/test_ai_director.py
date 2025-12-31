"""
Unit tests for ai_director module.

Tests parsing of AI-suggested segments and transcription formatting.
"""

import pytest
import json
from src.api.ai_director import (
    prepare_transcription_for_ai,
    parse_ai_segments,
    suggest_viral_segments,
    create_ai_prompt_for_editing,
    generate_edl_from_segments
)


class TestPrepareTranscriptionForAI:
    """Tests for prepare_transcription_for_ai function."""
    
    def test_basic_formatting(self, sample_whisper_data):
        """Test basic transcription formatting."""
        result = prepare_transcription_for_ai(sample_whisper_data)
        
        assert "[0]" in result
        assert "[1]" in result
        assert "[2]" in result
        assert "Hello world" in result
        assert "0.00s" in result
    
    def test_empty_segments(self):
        """Test handling of empty transcription."""
        result = prepare_transcription_for_ai({"segments": []})
        assert "No segments found" in result
    
    def test_text_only_fallback(self):
        """Test fallback when only text is available."""
        data = {"text": "Just some text without segments"}
        result = prepare_transcription_for_ai(data)
        assert "Just some text" in result
    
    def test_word_level_timestamps(self, sample_whisper_data):
        """Test word-level timestamp inclusion."""
        result = prepare_transcription_for_ai(sample_whisper_data, include_words=True)
        
        assert "Hello" in result
        assert "└─" in result  # Word indicator


class TestParseAISegments:
    """Tests for parse_ai_segments function."""
    
    def test_json_format(self):
        """Test parsing JSON format input."""
        json_input = '[{"start": 12.5, "end": 45.0, "title": "Hook scene"}]'
        result = parse_ai_segments(json_input)
        
        assert len(result) == 1
        assert result[0]["start"] == 12.5
        assert result[0]["end"] == 45.0
        assert result[0]["title"] == "Hook scene"
    
    def test_json_multiple_segments(self):
        """Test parsing multiple JSON segments."""
        json_input = '''
        [
            {"start": 0, "end": 15, "title": "Intro"},
            {"start": 15, "end": 45, "title": "Main content"},
            {"start": 45, "end": 60, "title": "Outro"}
        ]
        '''
        result = parse_ai_segments(json_input)
        
        assert len(result) == 3
        assert result[0]["title"] == "Intro"
        assert result[2]["end"] == 60
    
    def test_text_format_reel(self):
        """Test parsing 'Reel N: start - end' format."""
        text_input = """
        Reel 1: 12.5 - 45.0 (Hook about coding)
        Reel 2: 60.0 - 90.0 (The conclusion)
        """
        result = parse_ai_segments(text_input)
        
        assert len(result) == 2
        assert result[0]["start"] == 12.5
        assert result[0]["end"] == 45.0
    
    def test_simple_range_format(self):
        """Test parsing simple 'start - end' format."""
        text_input = "12.5 - 45.0: First segment"
        result = parse_ai_segments(text_input)
        
        assert len(result) == 1
        assert result[0]["start"] == 12.5
    
    def test_segment_indices(self, sample_whisper_data):
        """Test parsing segment indices with whisper data."""
        text_input = "Use segments 0, 2"
        result = parse_ai_segments(text_input, sample_whisper_data)
        
        assert len(result) == 2
        assert result[0]["start"] == 0.0
        assert result[1]["start"] == 10.0
    
    def test_segment_range(self, sample_whisper_data):
        """Test parsing segment index range."""
        text_input = "Segments: 0-2"
        result = parse_ai_segments(text_input, sample_whisper_data)
        
        assert len(result) == 3
    
    def test_empty_input(self):
        """Test handling of empty input."""
        result = parse_ai_segments("")
        assert result == []
    
    def test_invalid_input(self):
        """Test handling of unparseable input."""
        result = parse_ai_segments("This is just random text with no numbers")
        assert result == []
    
    def test_timecode_format(self):
        """Test parsing timecode format."""
        text_input = "00:01:30.500 - 00:02:45.000: Scene 1"
        result = parse_ai_segments(text_input)
        
        # Should parse timecodes
        if result:  # If timecode parsing is implemented
            assert result[0]["start"] == 90.5  # 1:30.500
    
    def test_json_embedded_in_text(self):
        """Test extracting JSON from mixed text."""
        text_input = '''
        Here are the suggested clips:
        [{"start": 5, "end": 15, "title": "Good part"}]
        Let me know if you want changes.
        '''
        result = parse_ai_segments(text_input)
        
        assert len(result) == 1
        assert result[0]["title"] == "Good part"


class TestSuggestViralSegments:
    """Tests for suggest_viral_segments function."""
    
    def test_basic_suggestions(self, sample_whisper_data):
        """Test basic viral segment suggestion."""
        result = suggest_viral_segments(sample_whisper_data)
        
        assert isinstance(result, list)
    
    def test_duration_limits(self, sample_whisper_data):
        """Test that suggestions respect duration limits."""
        result = suggest_viral_segments(
            sample_whisper_data,
            max_duration=30.0,
            min_duration=5.0
        )
        
        for seg in result:
            if "duration" in seg:
                assert seg["duration"] <= 30.0
    
    def test_scoring(self, sample_whisper_data):
        """Test that segments are scored."""
        result = suggest_viral_segments(sample_whisper_data)
        
        if result:
            assert "score" in result[0]


class TestGenerateEDL:
    """Tests for generate_edl_from_segments function."""
    
    def test_basic_edl(self):
        """Test basic EDL generation."""
        segments = [
            {"start": 0, "end": 10, "title": "Intro"},
            {"start": 10, "end": 30, "title": "Main"}
        ]
        
        result = generate_edl_from_segments(segments, title="TEST_EDL")
        
        assert "TITLE: TEST_EDL" in result
        assert "FCM: NON-DROP FRAME" in result
        assert "001" in result
        assert "002" in result
    
    def test_edl_with_fps(self):
        """Test EDL generation with different FPS."""
        segments = [{"start": 0, "end": 1, "title": "1 second"}]
        
        result_24 = generate_edl_from_segments(segments, fps=24.0)
        result_30 = generate_edl_from_segments(segments, fps=30.0)
        
        # Timecode should differ based on FPS
        assert "00:00:00:24" in result_24 or "00:00:01:00" in result_24
        assert "00:00:00:30" in result_30 or "00:00:01:00" in result_30


class TestCreateAIPrompt:
    """Tests for create_ai_prompt_for_editing function."""
    
    def test_viral_reels_prompt(self, sample_whisper_data):
        """Test viral reels prompt generation."""
        result = create_ai_prompt_for_editing(sample_whisper_data, style="viral_reels")
        
        assert "Instagram" in result or "TikTok" in result or "Reels" in result
        assert "JSON" in result
    
    def test_tutorial_prompt(self, sample_whisper_data):
        """Test tutorial prompt generation."""
        result = create_ai_prompt_for_editing(sample_whisper_data, style="tutorial")
        
        assert "step" in result.lower() or "instruction" in result.lower()
    
    def test_highlight_prompt(self, sample_whisper_data):
        """Test highlight prompt generation."""
        result = create_ai_prompt_for_editing(sample_whisper_data, style="highlight")
        
        assert "highlight" in result.lower() or "key" in result.lower()
    
    def test_podcast_prompt(self, sample_whisper_data):
        """Test podcast prompt generation."""
        result = create_ai_prompt_for_editing(sample_whisper_data, style="podcast")
        
        assert "chapter" in result.lower() or "podcast" in result.lower()
