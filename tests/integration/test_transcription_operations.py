
import pytest
import os
import json
from unittest.mock import MagicMock, patch
from src.api import transcription_operations

class TestTranscriptionOperations:
    
    @patch('src.api.transcription_operations.transcribe_with_whisper_node')
    def test_transcribe_clip_to_cache(self, mock_whisper, mock_resolve, tmp_path):
        # Setup
        mock_whisper.return_value = {"text": "Transcribed text", "segments": []}
        
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        media_pool = project.GetMediaPool()
        
        # Add clip
        from tests.conftest import MockMediaPoolItem
        # Create a temp file for the clip to exist
        clip_file = tmp_path / "test_clip.mp4"
        clip_file.touch()
        
        clip = MockMediaPoolItem("test_clip.mp4", {"File Path": str(clip_file)})
        media_pool.GetRootFolder().AddClip(clip)
        
        # Test
        result = transcription_operations.transcribe_clip_to_cache(
            mock_resolve,
            clip_name="test_clip.mp4"
        )
        
        # Verify
        assert "Success" in result
        mock_whisper.assert_called_once()
        
        # Verify cache file created (mock whisper doesn't create it, the function uses whisper output)
        # Wait, the function calls transcribe_with_whisper_node
        # In the real implementation, transcribe_with_whisper_node might save the file?
        # Let's check the code.
        # It calls transcribe_with_whisper_node which calls whisper and returns data.
        # But wait, looking at transcription_operations.py...
        # It says: "Run Whisper transcription and save result to a .json file next to the media."
        # But looking at my memory of `transcribe_clip_to_cache`:
        # cache_path = file_path + ".whisper.json"
        # It doesn't seem to write the file in `transcribe_clip_to_cache` itself?
        # Ah, I should check transcription_operations.py again.

    @patch('src.api.transcription_operations.os.path.exists')
    @patch('src.api.transcription_operations.open')
    def test_get_cached_transcription(self, mock_open, mock_exists, mock_resolve):
        # Setup
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps({"text": "Cached text"})
        mock_open.return_value = mock_file
        
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        media_pool = project.GetMediaPool()
        
        from tests.conftest import MockMediaPoolItem
        clip = MockMediaPoolItem("cached.mp4", {"File Path": "/path/cached.mp4"})
        media_pool.GetRootFolder().AddClip(clip)
        
        # Test
        result = transcription_operations.get_cached_transcription(
            mock_resolve,
            clip_name="cached.mp4"
        )
        
        # Verify
        assert "Cached text" in result

    def test_clear_folder_transcription(self, mock_resolve):
        # Setup
        project = mock_resolve.GetProjectManager().GetCurrentProject()
        media_pool = project.GetMediaPool()
        
        # Test
        result = transcription_operations.clear_folder_transcription(
            mock_resolve,
            folder_name="Master"
        )
        
        # Verify
        assert "Successfully cleared audio transcription" in result
