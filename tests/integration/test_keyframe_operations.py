
import pytest
from unittest.mock import MagicMock
from src.api import keyframe_operations

class TestKeyframeOperations:
    
    def test_add_keyframe(self, mock_resolve):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        
        # Add item to timeline
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip", start=100, end=200)
        timeline._video_tracks[0].append(item)
        item_id = item.GetUniqueId()
        
        # Test
        result = keyframe_operations.add_keyframe(
            mock_resolve, 
            timeline_item_id=item_id,
            property_name="ZoomX",
            frame=150,
            value=1.5
        )
        
        # Verify
        assert "Successfully added keyframe" in result
        assert item.GetKeyframeCount("ZoomX") == 1
        assert item.GetPropertyAtKeyframeIndex("ZoomX", 0) == 1.5

    def test_get_timeline_item_keyframes(self, mock_resolve):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip", start=0, end=100)
        timeline._video_tracks[0].append(item)
        item.AddKeyframe("ZoomX", 10, 1.0)
        item.AddKeyframe("ZoomX", 20, 1.5)
        item_id = item.GetUniqueId()
        
        # Test
        result = keyframe_operations.get_timeline_item_keyframes(
            mock_resolve,
            timeline_item_id=item_id,
            property_name="ZoomX"
        )
        
        # Verify
        assert "keyframes" in result
        assert "ZoomX" in result["keyframes"]
        assert len(result["keyframes"]["ZoomX"]) == 2
        assert result["keyframes"]["ZoomX"][1]["value"] == 1.5

    def test_modify_keyframe(self, mock_resolve):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip")
        timeline._video_tracks[0].append(item)
        item.AddKeyframe("ZoomX", 10, 1.0)
        item_id = item.GetUniqueId()
        
        # Test (Modify Value)
        result = keyframe_operations.modify_keyframe(
            mock_resolve,
            timeline_item_id=item_id,
            property_name="ZoomX",
            frame=10,
            new_value=2.0
        )
        
        # Verify
        assert "Successfully updated keyframe value" in result
        assert item.GetPropertyAtKeyframeIndex("ZoomX", 0) == 2.0
        
        # Test (Move Frame)
        result = keyframe_operations.modify_keyframe(
            mock_resolve,
            timeline_item_id=item_id,
            property_name="ZoomX",
            frame=10,
            new_frame=15
        )
        
        assert "Successfully moved keyframe" in result
        assert item.GetKeyframeAtIndex("ZoomX", 0)["frame"] == 15

    def test_delete_keyframe(self, mock_resolve):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip")
        timeline._video_tracks[0].append(item)
        item.AddKeyframe("ZoomX", 10, 1.0)
        item_id = item.GetUniqueId()
        
        # Test
        result = keyframe_operations.delete_keyframe(
            mock_resolve,
            timeline_item_id=item_id,
            property_name="ZoomX",
            frame=10
        )
        
        # Verify
        assert "Successfully deleted keyframe" in result
        assert item.GetKeyframeCount("ZoomX") == 0
