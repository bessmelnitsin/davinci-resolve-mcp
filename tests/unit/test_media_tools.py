"""
Unit tests for src/tools/media.py

Tests Media Pool operations using mock objects from conftest.py.
"""

import pytest
import sys
sys.path.insert(0, '.')

from tests.conftest import MockResolve, MockMediaPoolItem


class TestMediaTools:
    """Tests for Media Pool tools."""
    
    def test_mock_resolve_connection(self, mock_resolve):
        """Test that mock resolve connects properly."""
        assert mock_resolve is not None
        assert mock_resolve.GetProjectManager() is not None
        assert mock_resolve.GetProjectManager().GetCurrentProject() is not None
    
    def test_media_pool_access(self, mock_media_pool):
        """Test accessing the media pool."""
        assert mock_media_pool is not None
        root = mock_media_pool.GetRootFolder()
        assert root is not None
        assert root.GetName() == "Master"
    
    def test_import_media(self, mock_media_pool):
        """Test importing media files."""
        clips = mock_media_pool.ImportMedia(["/path/to/video.mp4"])
        assert len(clips) == 1
        assert clips[0].GetName() == "video.mp4"
        
        # Verify clip is in the folder
        root = mock_media_pool.GetRootFolder()
        clip_list = root.GetClipList()
        assert len(clip_list) == 1
    
    def test_create_subfolder(self, mock_media_pool):
        """Test creating a subfolder in media pool."""
        root = mock_media_pool.GetRootFolder()
        new_folder = mock_media_pool.AddSubFolder(root, "B-Roll")
        
        assert new_folder is not None
        assert new_folder.GetName() == "B-Roll"
        
        # Verify folder is in the hierarchy
        subfolders = root.GetSubFolderList()
        assert len(subfolders) == 1
        assert subfolders[0].GetName() == "B-Roll"
    
    def test_clip_properties(self):
        """Test getting and setting clip properties."""
        clip = MockMediaPoolItem("test_clip.mp4", {"FPS": "30", "Duration": "00:05:00:00"})
        
        assert clip.GetName() == "test_clip.mp4"
        assert clip.GetClipProperty("FPS") == "30"
        assert clip.GetClipProperty("Duration") == "00:05:00:00"
        
        # Set property
        clip.SetClipProperty("FPS", "24")
        assert clip.GetClipProperty("FPS") == "24"
    
    def test_sample_clips_fixture(self, sample_clips, mock_media_pool):
        """Test that sample clips fixture works."""
        assert len(sample_clips) == 4
        
        root = mock_media_pool.GetRootFolder()
        clips = root.GetClipList()
        assert len(clips) == 4
        
        clip_names = [c.GetName() for c in clips]
        assert "Interview_A.mp4" in clip_names
        assert "B-Roll_01.mp4" in clip_names
