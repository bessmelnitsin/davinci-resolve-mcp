
import pytest

# NOTE: src.api.transcription_operations module does not exist yet.
# These tests are skipped until the module is implemented.
# See task.md for details.

pytestmark = pytest.mark.skip(reason="src.api.transcription_operations module not yet implemented")


class TestTranscriptionOperations:

    def test_transcribe_clip_to_cache(self, mock_resolve, tmp_path):
        """Test transcribing a clip and caching the result."""
        pass

    def test_get_cached_transcription(self, mock_resolve):
        """Test retrieving a cached transcription."""
        pass

    def test_clear_folder_transcription(self, mock_resolve):
        """Test clearing transcription cache for a folder."""
        pass
