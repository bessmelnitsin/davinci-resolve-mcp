
import pytest
from unittest.mock import MagicMock
from src.api import timeline_operations

class TestTimelineOperations:
    
    def test_list_timelines(self, mock_resolve):
        # Setup - MockProject initializes with "Timeline 1"
        
        # Test
        timelines = timeline_operations.list_timelines(mock_resolve)
        
        # Verify
        assert len(timelines) > 0
        assert "Timeline 1" in timelines

    def test_get_current_timeline_info(self, mock_resolve):
        # Test
        info = timeline_operations.get_current_timeline_info(mock_resolve)
        
        # Verify
        assert info["name"] == "Timeline 1"
        assert "resolution" in info
        assert "framerate" in info

    def test_create_timeline(self, mock_resolve):
        # Test
        result = timeline_operations.create_timeline(mock_resolve, "New Timeline")
        
        # Verify
        assert "Successfully created timeline 'New Timeline'" in result
        
        # Verify it exists
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        assert project.GetTimelineCount() == 2  # Original + New

    def test_create_empty_timeline_custom(self, mock_resolve):
        # Test
        result = timeline_operations.create_empty_timeline(
            mock_resolve, 
            "Custom Timeline",
            frame_rate="30",
            resolution_width=3840,
            resolution_height=2160
        )
        
        # Verify
        assert "Successfully created timeline" in result
        
        # Verify settings were set on the new timeline
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        assert timeline.GetSetting("timelineFrameRate") == "30"
        assert timeline.GetSetting("timelineResolutionWidth") == "3840"

    def test_set_current_timeline(self, mock_resolve):
        # Setup
        timeline_operations.create_timeline(mock_resolve, "Second Timeline")
        
        # Test
        result = timeline_operations.set_current_timeline(mock_resolve, "Second Timeline")
        
        # Verify
        assert "Successfully switched" in result
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        assert project.GetCurrentTimeline().GetName() == "Second Timeline"

    def test_add_marker(self, mock_resolve):
        # Setup - Add clip to timeline
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip", start=0, end=100)
        timeline._video_tracks[0].append(item)
        
        # Test
        result = timeline_operations.add_marker(
            mock_resolve,
            frame=10,
            color="Red",
            note="Test Marker"
        )
        
        # Verify
        assert "Successfully added Red marker" in result
        markers = timeline.GetMarkers()
        assert 10 in markers
        assert markers[10]["name"] == "Test Marker"  # Note becomes name in mock

    def test_delete_timeline(self, mock_resolve):
        # Setup - create timeline to delete
        timeline_operations.create_timeline(mock_resolve, "To Delete")
        
        # Test
        result = timeline_operations.delete_timeline(mock_resolve, "To Delete")
        
        # Verify
        assert "Successfully deleted timeline" in result
        timelines = timeline_operations.list_timelines(mock_resolve)
        assert "To Delete" not in timelines

    def test_get_timeline_tracks(self, mock_resolve):
        # Test
        tracks = timeline_operations.get_timeline_tracks(mock_resolve)
        
        # Verify
        assert "video" in tracks
        assert "audio" in tracks
        assert tracks["video"]["count"] == 1
        assert len(tracks["video"]["tracks"]) == 1
        assert tracks["video"]["tracks"][0]["name"] == "V1"
