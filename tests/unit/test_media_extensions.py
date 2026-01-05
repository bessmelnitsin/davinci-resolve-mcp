import pytest
from unittest.mock import MagicMock, patch
from src.tools.media import (
    import_folder_from_drb, 
    delete_folder,
    get_folder_is_stale,
    export_folder_to_drb
)

# Mock the get_resolve function used by tools
@pytest.fixture
def mock_get_resolve(mock_resolve):
    with patch("src.tools.media.get_resolve", return_value=mock_resolve):
        yield mock_resolve

def test_import_folder_from_drb(mock_get_resolve, mock_resolve):
    """Test importing a folder from a DRB file."""
    # Setup
    pm = mock_resolve.GetProjectManager()
    project = pm.CreateProject("Test Project")
    media_pool = project.GetMediaPool()
    
    # Test
    result = import_folder_from_drb("/path/to/backup.drb")
    
    # Verify
    assert "Successfully imported folder" in result
    root_folder = media_pool.GetRootFolder()
    subfolders = root_folder.GetSubFolderList()
    assert len(subfolders) == 1
    assert subfolders[0].GetName() == "backup"

def test_delete_folder(mock_get_resolve, mock_resolve):
    """Test deleting a folder."""
    # Setup
    pm = mock_resolve.GetProjectManager()
    project = pm.CreateProject("Test Project")
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    media_pool.AddSubFolder(root_folder, "To Delete")
    
    # Verify creation
    assert len(root_folder.GetSubFolderList()) > 0
    
    # Test
    result = delete_folder("To Delete")
    
    # Verify deletion
    assert "Deleted folder" in result
    assert len(root_folder.GetSubFolderList()) == 0

def test_get_folder_is_stale(mock_get_resolve, mock_resolve):
    """Test checking if a folder is stale."""
    # Setup
    pm = mock_resolve.GetProjectManager()
    project = pm.CreateProject("Test Project")
    
    # Test
    result = get_folder_is_stale("Master")
    
    # Verify
    assert "is_stale" in result
    assert result["is_stale"] is False

def test_export_folder_to_drb(mock_get_resolve, mock_resolve):
    """Test exporting a folder."""
    # Setup
    pm = mock_resolve.GetProjectManager()
    project = pm.CreateProject("Test Project")
    
    # Test
    result = export_folder_to_drb("Master", "/output/path.drb")
    
    # Verify
    assert "Exported folder" in result
