
import pytest
import os
from unittest.mock import MagicMock, patch
from src.api import export_operations

class TestExportOperations:
    
    def test_get_lut_formats(self, mock_resolve):
        # Test
        formats = export_operations.get_lut_formats(mock_resolve)
        
        # Verify
        assert "formats" in formats
        assert "sizes" in formats
        assert isinstance(formats["formats"], list)
        assert any(f["name"] == "Cube" for f in formats["formats"])

    def test_export_lut(self, mock_resolve, tmp_path):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        timeline = project.GetCurrentTimeline()
        
        # Add item to timeline
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip")
        timeline._video_tracks[0].append(item)
        
        export_path = os.path.join(tmp_path, "test_lut.cube")
        
        # Test
        result = export_operations.export_lut(
            mock_resolve, 
            clip_name="TestClip", 
            export_path=export_path
        )
        
        # Verify
        assert "Successfully exported LUT" in result
        
    def test_export_all_powergrade_luts(self, mock_resolve, tmp_path):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        gallery = project.GetGallery()
        albums = gallery.GetAlbums()
        
        # Find PowerGrade album (mock creates it in init)
        pg_album = next((a for a in albums if a.GetName() == "PowerGrade"), None)
        assert pg_album is not None
        
        # Create a MockStill in PowerGrade album
        from tests.conftest import MockStill
        still = MockStill("pg_1", "My Grade")
        pg_album.AddStill(still)
        
        # Also need a clip on timeline for it to apply to
        timeline = project.GetCurrentTimeline()
        from tests.conftest import MockTimelineItem
        item = MockTimelineItem("TestClip")
        timeline._video_tracks[0].append(item)
        
        # Test
        result = export_operations.export_all_powergrade_luts(mock_resolve, str(tmp_path))
        
        # Verify
        assert "Successfully exported all 1 PowerGrade LUTs" in result
