"""
Unit tests for src/tools/timeline.py

Tests Timeline operations using mock objects from conftest.py.
"""

import pytest
import sys
sys.path.insert(0, '.')

from tests.conftest import MockResolve, MockTimeline, MockTimelineItem


class TestTimelineTools:
    """Tests for Timeline tools."""
    
    def test_timeline_access(self, mock_timeline):
        """Test accessing timeline."""
        assert mock_timeline is not None
        assert mock_timeline.GetName() == "Timeline 1"
    
    def test_timeline_settings(self, mock_timeline):
        """Test getting timeline settings."""
        fps = mock_timeline.GetSetting("timelineFrameRate")
        width = mock_timeline.GetSetting("timelineResolutionWidth")
        height = mock_timeline.GetSetting("timelineResolutionHeight")
        
        assert fps == "24"
        assert width == "1920"
        assert height == "1080"
    
    def test_set_timeline_settings(self, mock_timeline):
        """Test setting timeline settings."""
        mock_timeline.SetSetting("timelineFrameRate", "30")
        assert mock_timeline.GetSetting("timelineFrameRate") == "30"
    
    def test_track_count(self, mock_timeline):
        """Test getting track counts."""
        video_tracks = mock_timeline.GetTrackCount("video")
        audio_tracks = mock_timeline.GetTrackCount("audio")
        
        assert video_tracks >= 1
        assert audio_tracks >= 1
    
    def test_add_track(self, mock_timeline):
        """Test adding tracks."""
        initial_video = mock_timeline.GetTrackCount("video")
        mock_timeline.AddTrack("video")
        assert mock_timeline.GetTrackCount("video") == initial_video + 1
        
        initial_audio = mock_timeline.GetTrackCount("audio")
        mock_timeline.AddTrack("audio")
        assert mock_timeline.GetTrackCount("audio") == initial_audio + 1
    
    def test_add_marker(self, mock_timeline):
        """Test adding markers."""
        result = mock_timeline.AddMarker(100, "Blue", "Test Marker", "This is a test")
        assert result is True
        
        markers = mock_timeline.GetMarkers()
        assert 100 in markers
        assert markers[100]["color"] == "Blue"
        assert markers[100]["name"] == "Test Marker"
    
    def test_timeline_frame_range(self, mock_timeline):
        """Test getting timeline frame range."""
        start = mock_timeline.GetStartFrame()
        end = mock_timeline.GetEndFrame()
        
        assert start == 0
        assert end == 1000
    
    def test_timeline_item_properties(self):
        """Test timeline item properties."""
        item = MockTimelineItem("Clip 1", start=0, end=100)
        
        assert item.GetName() == "Clip 1"
        assert item.GetStart() == 0
        assert item.GetEnd() == 100
        assert item.GetDuration() == 100
        assert item.GetType() == "Video"
    
    def test_timeline_item_keyframes(self):
        """Test adding keyframes to timeline items."""
        item = MockTimelineItem("Clip with Keyframes")
        
        # Add keyframes
        item.AddKeyframe("ZoomX", 0, 1.0)
        item.AddKeyframe("ZoomX", 50, 1.5)
        item.AddKeyframe("ZoomX", 100, 1.0)
        
        assert item.GetKeyframeCount("ZoomX") == 3
        assert item.GetPropertyAtKeyframeIndex("ZoomX", 0) == 1.0
        assert item.GetPropertyAtKeyframeIndex("ZoomX", 1) == 1.5
        
        # Delete keyframe
        item.DeleteKeyframe("ZoomX", 50)
        assert item.GetKeyframeCount("ZoomX") == 2
