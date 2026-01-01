
import pytest
from unittest.mock import MagicMock
from src.api import gallery_operations

class TestGalleryOperations:
    
    def test_get_color_presets(self, mock_resolve):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        gallery = project.GetGallery()
        album = gallery.GetAlbums()[0]
        
        # Add a still to the album
        gallery._current_album = album
        gallery.GrabStill()
        
        # Test
        presets = gallery_operations.get_color_presets(mock_resolve)
        
        # Verify
        assert len(presets) > 0
        assert presets[0]["name"] == "DaVinci Resolve"
        assert len(presets[0]["stills"]) > 0
        assert "Still 1" in presets[0]["stills"][0]["label"]

    def test_create_color_preset_album(self, mock_resolve):
        # Test
        result = gallery_operations.create_color_preset_album(mock_resolve, "New Album")
        
        # Verify
        assert "Successfully created album 'New Album'" in result
        
        # Verify album exists in gallery
        gallery = mock_resolve.GetProjectManager().GetCurrentProject().GetGallery()
        albums = gallery.GetAlbums()
        assert any(a.GetName() == "New Album" for a in albums)

    def test_save_color_preset(self, mock_resolve):
        # Setup - ensure we have a timeline and a clip
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        timeline.AddTrack("video")
        
        # This relies on MockTimeline.GetCurrentVideoItem returning something
        # In our mock it returns items[0][0] if exists.
        # We need to add an item to the track
        # But MockTimeline._video_tracks is initialized with [[]] so first track is empty.
        # Let's add an item
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip")
        timeline._video_tracks[0].append(item)
        
        # Test
        result = gallery_operations.save_color_preset(mock_resolve, preset_name="My Preset")
        
        # Verify
        assert "Successfully saved color preset 'My Preset'" in result
        
        # Verify it was added to the default album
        gallery = project.GetGallery()
        album = gallery.GetCurrentStillAlbum()
        stills = album.GetStills()
        assert stills[-1].GetLabel() == "My Preset"

    def test_delete_color_preset_album(self, mock_resolve):
        # Setup
        gallery_operations.create_color_preset_album(mock_resolve, "To Delete")
        
        # Test
        result = gallery_operations.delete_color_preset_album(mock_resolve, "To Delete")
        
        # Verify
        assert "Successfully deleted album 'To Delete'" in result
        
        gallery = mock_resolve.GetProjectManager().GetCurrentProject().GetGallery()
        albums = gallery.GetAlbums()
        assert not any(a.GetName() == "To Delete" for a in albums)

    def test_apply_color_preset(self, mock_resolve):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        gallery = project.GetGallery()
        
        # Add a still
        gallery.GrabStill()
        stills = gallery.GetCurrentStillAlbum().GetStills()
        stills[-1].SetLabel("TestPreset")
        
        # Setup timeline
        timeline = project.GetCurrentTimeline()
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip")
        timeline._video_tracks[0].append(item)
        
        # Test
        result = gallery_operations.apply_color_preset(mock_resolve, preset_name="TestPreset")
        
        # Verify
        assert "Successfully applied color preset" in result

    def test_delete_color_preset(self, mock_resolve):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        gallery = project.GetGallery()
        
        # Add a still
        gallery.GrabStill()
        stills = gallery.GetCurrentStillAlbum().GetStills()
        stills[-1].SetLabel("ToDelete")
        initial_count = len(stills)
        
        # Test
        result = gallery_operations.delete_color_preset(mock_resolve, preset_name="ToDelete")
        
        # Verify
        assert "Successfully deleted color preset" in result
        assert len(gallery.GetCurrentStillAlbum().GetStills()) == initial_count - 1
