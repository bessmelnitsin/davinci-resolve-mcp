"""
Unit tests for error_handling module.

Tests custom exceptions and decorators.
"""

import pytest
from unittest.mock import MagicMock

from src.utils.error_handling import (
    # Exceptions
    ResolveAPIError,
    ResolveNotConnectedError,
    ProjectNotOpenError,
    TimelineNotFoundError,
    NoCurrentTimelineError,
    ClipNotFoundError,
    RenderError,
    # Decorators
    require_resolve,
    require_project,
    require_timeline,
    safe_api_call,
    # Helpers
    get_project_safe,
    get_timeline_safe,
    format_error_response
)


class TestCustomExceptions:
    """Tests for custom exception classes."""
    
    def test_resolve_api_error_basic(self):
        """Test basic ResolveAPIError."""
        error = ResolveAPIError("Test error")
        
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.suggestion is None
    
    def test_resolve_api_error_with_suggestion(self):
        """Test ResolveAPIError with suggestion."""
        error = ResolveAPIError("Test error", suggestion="Try this fix")
        
        result = error.to_dict()
        assert result["error"] == "Test error"
        assert result["suggestion"] == "Try this fix"
    
    def test_resolve_not_connected_error(self):
        """Test ResolveNotConnectedError defaults."""
        error = ResolveNotConnectedError()
        
        assert "не подключен" in error.message.lower() or "not connected" in error.message.lower()
        assert error.suggestion is not None
    
    def test_project_not_open_error(self):
        """Test ProjectNotOpenError defaults."""
        error = ProjectNotOpenError()
        
        assert "не открыт" in error.message.lower() or "not open" in error.message.lower()
        assert "open_project" in error.suggestion.lower() or "create_project" in error.suggestion.lower()
    
    def test_timeline_not_found_error(self):
        """Test TimelineNotFoundError with name."""
        error = TimelineNotFoundError("My Timeline")
        
        assert "My Timeline" in error.message
    
    def test_clip_not_found_error(self):
        """Test ClipNotFoundError with name."""
        error = ClipNotFoundError("clip_001.mp4")
        
        assert "clip_001.mp4" in error.message


class TestRequireResolveDecorator:
    """Tests for require_resolve decorator."""
    
    def test_with_valid_resolve(self, mock_resolve):
        """Test decorator passes with valid resolve."""
        @require_resolve
        def test_function(resolve):
            return "success"
        
        result = test_function(mock_resolve)
        assert result == "success"
    
    def test_with_none_resolve(self):
        """Test decorator raises with None resolve."""
        @require_resolve
        def test_function(resolve):
            return "success"
        
        with pytest.raises(ResolveNotConnectedError):
            test_function(None)
    
    def test_preserves_function_args(self, mock_resolve):
        """Test decorator preserves additional arguments."""
        @require_resolve
        def test_function(resolve, arg1, kwarg1=None):
            return f"{arg1}-{kwarg1}"
        
        result = test_function(mock_resolve, "test", kwarg1="value")
        assert result == "test-value"


class TestRequireProjectDecorator:
    """Tests for require_project decorator."""
    
    def test_with_valid_project(self, mock_resolve):
        """Test decorator passes with valid project."""
        @require_project
        def test_function(resolve):
            return "success"
        
        result = test_function(mock_resolve)
        assert result == "success"
    
    def test_with_none_resolve(self):
        """Test decorator raises with None resolve."""
        @require_project
        def test_function(resolve):
            return "success"
        
        with pytest.raises(ResolveNotConnectedError):
            test_function(None)
    
    def test_with_no_project(self):
        """Test decorator raises when no project open."""
        mock_resolve = MagicMock()
        mock_pm = MagicMock()
        mock_pm.GetCurrentProject.return_value = None
        mock_resolve.GetProjectManager.return_value = mock_pm
        
        @require_project
        def test_function(resolve):
            return "success"
        
        with pytest.raises(ProjectNotOpenError):
            test_function(mock_resolve)


class TestRequireTimelineDecorator:
    """Tests for require_timeline decorator."""
    
    def test_with_valid_timeline(self, mock_resolve):
        """Test decorator passes with valid timeline."""
        @require_timeline
        def test_function(resolve):
            return "success"
        
        result = test_function(mock_resolve)
        assert result == "success"
    
    def test_with_no_timeline(self, mock_resolve):
        """Test decorator raises when no timeline active."""
        # Modify mock to have no timeline
        mock_resolve.GetProjectManager().GetCurrentProject()._current_timeline = None
        
        @require_timeline
        def test_function(resolve):
            return "success"
        
        with pytest.raises(NoCurrentTimelineError):
            test_function(mock_resolve)


class TestSafeApiCallDecorator:
    """Tests for safe_api_call decorator."""
    
    def test_successful_call(self):
        """Test decorator passes through successful calls."""
        @safe_api_call()
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_catches_exception(self):
        """Test decorator catches and handles exceptions."""
        @safe_api_call()
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert "error" in result
    
    def test_returns_default(self):
        """Test decorator returns default value on error."""
        @safe_api_call(default_return=[])
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result == []
    
    def test_handles_resolve_api_error(self):
        """Test decorator handles ResolveAPIError specially."""
        @safe_api_call()
        def test_function():
            raise ResolveAPIError("Custom error", suggestion="Try this")
        
        result = test_function()
        assert result["error"] == "Custom error"
        assert result["suggestion"] == "Try this"


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_get_project_safe_success(self, mock_resolve):
        """Test get_project_safe with valid setup."""
        success, project, message = get_project_safe(mock_resolve)
        
        assert success is True
        assert project is not None
        assert message == "OK"
    
    def test_get_project_safe_no_resolve(self):
        """Test get_project_safe with None resolve."""
        success, project, message = get_project_safe(None)
        
        assert success is False
        assert project is None
        assert "не подключен" in message.lower() or "not connected" in message.lower()
    
    def test_get_timeline_safe_success(self, mock_resolve):
        """Test get_timeline_safe with valid setup."""
        success, timeline, message = get_timeline_safe(mock_resolve)
        
        assert success is True
        assert timeline is not None
        assert message == "OK"
    
    def test_format_error_response_string(self):
        """Test format_error_response with string error."""
        result = format_error_response("Something went wrong")
        
        assert result["error"] == "Something went wrong"
    
    def test_format_error_response_exception(self):
        """Test format_error_response with exception."""
        error = ValueError("Test error")
        result = format_error_response(error, suggestion="Try again")
        
        assert "Test error" in result["error"]
        assert result["suggestion"] == "Try again"
    
    def test_format_error_response_with_context(self):
        """Test format_error_response with context."""
        result = format_error_response(
            "Error occurred",
            context={"clip": "test.mp4", "operation": "import"}
        )
        
        assert result["context"]["clip"] == "test.mp4"
