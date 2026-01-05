import pytest
from unittest.mock import MagicMock, patch
from src.tools.color import (
    get_node_label,
    get_node_lut,
    delete_gallery_stills,
    get_gallery_still_label,
    set_gallery_still_label
)

# Mock the get_resolve function used by tools
@pytest.fixture
def mock_get_resolve(mock_resolve):
    with patch("src.tools.color.get_resolve", return_value=mock_resolve):
        yield mock_resolve

def test_get_node_label(mock_get_resolve, mock_resolve):
    """Test getting node label."""
    # Setup
    pm = mock_resolve.GetProjectManager()
    project = pm.CreateProject("Test Project")
    timeline = project.GetCurrentTimeline()
    timeline.AddTrack("video")
    
    # Needs a clip in timeline
    clip = MagicMock() # Should be MockTimelineItem ideally but we rely on conftest fixtures if possible
    # MockTimeline.GetCurrentVideoItem returns first item in first track.
    # So we need to add an item to the mocked timeline fixture
    pass

    # Actually, let's use the full mock structure
    # The tool calls timeline.GetCurrentVideoItem(). Returns MockTimelineItem.
    # MockTimelineItem.GetCurrentGrade() returns MockGrade.
    # MockGrade.GetNodeLabel(index) returns "Label {index}".
    
    # We need to ensure GetCurrentVideoItem returns something.
    # MockTimeline.GetCurrentVideoItem implementation:
    # if self._video_tracks and self._video_tracks[0]: return self._video_tracks[0][0]
    
    # So we must add an item.
    clip = MagicMock() 
    # But wait, our conftest MockTimelineItem is better.
    from tests.conftest import MockTimelineItem
    clip = MockTimelineItem("Test Clip")
    timeline._video_tracks[0].append(clip)
    
    # Test
    result = get_node_label(1)
    
    # Verify
    assert "label" in result
    assert result["label"] == "Label 1"

def test_get_node_lut(mock_get_resolve, mock_resolve):
    """Test getting node LUT."""
    # Setup
    pm = mock_resolve.GetProjectManager()
    project = pm.CreateProject("Test Project")
    timeline = project.GetCurrentTimeline()
    timeline.AddTrack("video")
    from tests.conftest import MockTimelineItem
    clip = MockTimelineItem("Test Clip")
    timeline._video_tracks[0].append(clip)
    
    # Test
    result = get_node_lut(2)
    
    # Verify
    assert "lut" in result
    assert result["lut"] == "LUT_2.cube"

def test_gallery_stills_operations(mock_get_resolve, mock_resolve):
    """Test gallery still operations."""
    # Setup
    pm = mock_resolve.GetProjectManager()
    project = pm.CreateProject("Test Project")
    gallery = project.GetGallery()
    
    # Create an album and add a still
    album = gallery.CreateAlbum("Test Album")
    gallery.GrabStill() # Adds strict still to current album (which is default album? need to set?)
    # MockGallery.__init__ sets current album to first album.
    # CreateAlbum appends.
    # We need to switch to Test Album if we want to test that specific one, or just use default.
    
    # Let's interact with default album
    gallery.GrabStill()
    stills = gallery.GetCurrentStillAlbum().GetStills()
    still_index = 0
    
    # Test Get Label
    result = get_gallery_still_label(still_index)
    assert result["label"] == "Still 1"
    
    # Test Set Label
    result_set = set_gallery_still_label("New Label", still_index)
    assert "New Label" in result_set
    assert stills[0].GetLabel() == "New Label"
    
    # Test Delete Still
    # Using label since that's what the tool likely uses or supports?
    # Tool supports label list.
    result_del = delete_gallery_stills(still_labels=["New Label"])
    assert "Deleted" in result_del
