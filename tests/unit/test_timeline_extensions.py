
"""
Unit tests for new timeline extension tools.
"""

import pytest
import sys
sys.path.insert(0, '.')

from src.api.timeline_operations import (
    get_timeline_mark_in_out,
    set_timeline_mark_in_out,
    clear_timeline_mark_in_out,
    get_track_sub_type
)

class TestTimelineExtensions:
    """Tests for Timeline extension tools."""
    
    def test_get_timeline_mark_in_out(self, mock_resolve, mock_timeline):
        """Test getting timeline mark in/out."""
        result = get_timeline_mark_in_out(mock_resolve)
        assert result == {"in": 0, "out": 100}
        
        # Test with timeline name (mock logic handles finding current timeline)
        result_named = get_timeline_mark_in_out(mock_resolve, "Timeline 1")
        assert result_named == {"in": 0, "out": 100}

    def test_set_timeline_mark_in_out(self, mock_resolve, mock_timeline):
        """Test setting timeline mark in/out."""
        result = set_timeline_mark_in_out(mock_resolve, 10, 50, "video")
        assert "Set mark in/out (video): 10-50" in result

    def test_clear_timeline_mark_in_out(self, mock_resolve, mock_timeline):
        """Test clearing timeline mark in/out."""
        result = clear_timeline_mark_in_out(mock_resolve, "all")
        assert "Cleared mark in/out (all)" in result

    def test_get_track_sub_type(self, mock_resolve, mock_timeline):
        """Test getting track sub-type."""
        result = get_track_sub_type(mock_resolve, "audio", 1)
        assert result == "stereo"

from src.api.timeline_operations import (
    get_timeline_item_source_start_end,
    get_timeline_item_fusion_comp_by_index,
    delete_take_by_index,
    get_timeline_item_version
)

class TestTimelineItemExtensions:
    """Tests for TimelineItem extension tools."""
    
    def test_get_timeline_item_source_start_end(self, mock_resolve, mock_timeline):
        """Test getting source start/end."""
        # Ensure the mock timeline has items
        mock_timeline.AddTrack("video") 
        # (MockTimeline usually init with 1 video track with items in conftest?)
        # Let's check conftest logic... GetItemListInTrack returns list of MockTimelineItem?
        # conftest: self._video_tracks = [[]] init.
        # So we need to add an item.
        item = mock_resolve.GetProjectManager().GetCurrentProject().GetCurrentTimeline().GetItemListInTrack("video", 1)
        # Wait, MockTimeline init: self._video_tracks = [[]]. No items by default?
        # Let's add an item to the mock track 1 manually for this test context.
        timeline = mock_resolve.GetProjectManager().GetCurrentProject().GetCurrentTimeline()
        from tests.conftest import MockTimelineItem
        newItem = MockTimelineItem("Clip 1")
        timeline._video_tracks[0].append(newItem)
        
        result = get_timeline_item_source_start_end(mock_resolve, item_index=1)
        assert result["source_start"] == 0
        assert result["source_end"] == 100

    def test_get_timeline_item_fusion_comp(self, mock_resolve):
        """Test getting fusion comp."""
        timeline = mock_resolve.GetProjectManager().GetCurrentProject().GetCurrentTimeline()
        # Item already added in previous test or fixture? Sharing fixture state.
        # Safest to add again or check.
        if not timeline._video_tracks[0]:
             from tests.conftest import MockTimelineItem
             timeline._video_tracks[0].append(MockTimelineItem("Clip 1"))
        
        timeline._video_tracks[0][0].AddFusionComp()
        
        result = get_timeline_item_fusion_comp_by_index(mock_resolve, 1, 1)
        # Mock fusion comp returns magic mock, name might default or be settable?
        # In conftest: item.GetFusionCompByIndex returns self._fusion_comps[i]. 
        # .GetName() on MagicMock returns another MagicMock usually unless configured.
        # But our tool code calls .GetName(). 
        # Let's let it return the mock name.
        assert "name" in result

    def test_delete_take_by_index(self, mock_resolve):
        """Test delete take."""
        timeline = mock_resolve.GetProjectManager().GetCurrentProject().GetCurrentTimeline()
        if not timeline._video_tracks[0]:
             from tests.conftest import MockTimelineItem
             timeline._video_tracks[0].append(MockTimelineItem("Clip 1"))
             
        result = delete_take_by_index(mock_resolve, 1, 1)
        assert "Deleted take 1" in result

    def test_get_timeline_item_version(self, mock_resolve):
        """Test get item version."""
        timeline = mock_resolve.GetProjectManager().GetCurrentProject().GetCurrentTimeline()
        if not timeline._video_tracks[0]:
             from tests.conftest import MockTimelineItem
             timeline._video_tracks[0].append(MockTimelineItem("Clip 1"))
             
        result = get_timeline_item_version(mock_resolve, 1)
        assert result["current_version"] == "Version 1"

