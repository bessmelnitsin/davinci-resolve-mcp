"""
Unit tests for src/tools/project.py

Tests Project operations using mock objects from conftest.py.
"""

import pytest
import sys
sys.path.insert(0, '.')

from tests.conftest import MockResolve, MockProject


class TestProjectTools:
    """Tests for Project tools."""
    
    def test_project_manager_access(self, mock_resolve):
        """Test accessing project manager."""
        pm = mock_resolve.GetProjectManager()
        assert pm is not None
    
    def test_current_project(self, mock_project):
        """Test getting current project."""
        assert mock_project is not None
        assert mock_project.GetName() == "Test Project"
    
    def test_project_list(self, mock_resolve):
        """Test listing projects."""
        pm = mock_resolve.GetProjectManager()
        projects = pm.GetProjectListInCurrentFolder()
        
        assert len(projects) >= 1
        assert "Test Project" in projects
    
    def test_create_project(self, mock_resolve):
        """Test creating a new project."""
        pm = mock_resolve.GetProjectManager()
        new_project = pm.CreateProject("New Test Project")
        
        assert new_project is not None
        assert new_project.GetName() == "New Test Project"
        
        # Verify it's in the list
        projects = pm.GetProjectListInCurrentFolder()
        assert "New Test Project" in projects
    
    def test_load_project(self, mock_resolve):
        """Test loading a project."""
        pm = mock_resolve.GetProjectManager()
        
        # Create another project first
        pm.CreateProject("Another Project")
        
        # Load the original project
        loaded = pm.LoadProject("Test Project")
        assert loaded is not None
        assert loaded.GetName() == "Test Project"
    
    def test_project_settings(self, mock_project):
        """Test getting and setting project settings."""
        # Set a setting
        mock_project.SetSetting("CacheMode", "1")
        assert mock_project.GetSetting("CacheMode") == "1"
        
        mock_project.SetSetting("ProxyMode", "0")
        assert mock_project.GetSetting("ProxyMode") == "0"
    
    def test_project_timelines(self, mock_project):
        """Test project timeline operations."""
        count = mock_project.GetTimelineCount()
        assert count >= 1
        
        timeline = mock_project.GetTimelineByIndex(1)
        assert timeline is not None
        assert timeline.GetName() == "Timeline 1"
    
    def test_set_current_timeline(self, mock_project):
        """Test setting current timeline."""
        timeline = mock_project.GetTimelineByIndex(1)
        result = mock_project.SetCurrentTimeline(timeline)
        
        assert result is True
        assert mock_project.GetCurrentTimeline() == timeline
    
    def test_render_jobs(self, mock_project):
        """Test render job operations."""
        # Initially no jobs
        jobs = mock_project.GetRenderJobList()
        initial_count = len(jobs)
        
        # Add a job
        job_id = mock_project.AddRenderJob()
        assert job_id is not None
        
        jobs = mock_project.GetRenderJobList()
        assert len(jobs) == initial_count + 1
        
        # Clear jobs
        mock_project.DeleteAllRenderJobs()
        assert len(mock_project.GetRenderJobList()) == 0
