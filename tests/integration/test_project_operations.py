
import pytest
from unittest.mock import MagicMock
from src.api import project_operations

class TestProjectOperations:
    
    def test_list_projects(self, mock_resolve):
        # Setup
        project_manager = mock_resolve.GetProjectManager()
        # MockProjectManager initializes with "Test Project"
        
        # Test
        projects = project_operations.list_projects(mock_resolve)
        
        # Verify
        assert len(projects) > 0
        assert "Test Project" in projects

    def test_get_current_project_name(self, mock_resolve):
        # Test
        name = project_operations.get_current_project_name(mock_resolve)
        
        # Verify
        assert name == "Test Project"
        
    def test_create_project(self, mock_resolve):
        # Test
        result = project_operations.create_project(mock_resolve, "New Project")
        
        # Verify
        assert "Successfully created project" in result
        
        # Verify it exists
        project_manager = mock_resolve.GetProjectManager()
        assert "New Project" in project_manager.GetProjectListInCurrentFolder()
        assert project_manager.GetCurrentProject().GetName() == "New Project"

    def test_open_project(self, mock_resolve):
        # Setup - create a project first
        project_manager = mock_resolve.GetProjectManager()
        project_manager.CreateProject("Project B")
        
        # Ensure we are not on Project B
        project_manager.LoadProject("Test Project")
        assert project_manager.GetCurrentProject().GetName() == "Test Project"
        
        # Test
        result = project_operations.open_project(mock_resolve, "Project B")
        
        # Verify
        assert "Successfully opened project" in result
        assert project_manager.GetCurrentProject().GetName() == "Project B"

    def test_save_project(self, mock_resolve):
        # Test
        result = project_operations.save_project(mock_resolve)
        
        # Verify
        assert "Project 'Test Project' is saved" in result
