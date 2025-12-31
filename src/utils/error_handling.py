#!/usr/bin/env python3
"""
Centralized Error Handling for DaVinci Resolve MCP

Provides:
- Custom exception classes for API errors
- Decorators for common checks (require_resolve, require_project, etc.)
- Safe API call wrappers with logging
"""

import logging
from functools import wraps
from typing import Callable, Any, TypeVar, Optional, Tuple, Union

logger = logging.getLogger("davinci-resolve-mcp.errors")

# Type variable for preserving function signatures
F = TypeVar('F', bound=Callable[..., Any])


# =====================
# Custom Exceptions
# =====================

class ResolveAPIError(Exception):
    """Base class for all DaVinci Resolve API errors."""
    
    def __init__(self, message: str, suggestion: str = None):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
    
    def to_dict(self) -> dict:
        result = {"error": self.message}
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


class ResolveNotConnectedError(ResolveAPIError):
    """Raised when DaVinci Resolve is not running or not connected."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message or "DaVinci Resolve не подключен",
            suggestion="Убедитесь, что DaVinci Resolve запущен перед использованием MCP сервера"
        )


class ProjectNotOpenError(ResolveAPIError):
    """Raised when no project is currently open."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message or "Проект не открыт",
            suggestion="Используйте open_project('имя') или create_project('имя') для открытия проекта"
        )


class TimelineNotFoundError(ResolveAPIError):
    """Raised when the specified timeline cannot be found."""
    
    def __init__(self, timeline_name: str = None):
        message = f"Timeline '{timeline_name}' не найден" if timeline_name else "Timeline не найден"
        super().__init__(
            message,
            suggestion="Используйте list_timelines() чтобы увидеть доступные timelines"
        )


class NoCurrentTimelineError(ResolveAPIError):
    """Raised when there's no current timeline set."""
    
    def __init__(self):
        super().__init__(
            "Нет активного timeline",
            suggestion="Создайте timeline с create_timeline('имя') или выберите с set_current_timeline('имя')"
        )


class ClipNotFoundError(ResolveAPIError):
    """Raised when the specified clip cannot be found in Media Pool."""
    
    def __init__(self, clip_name: str = None):
        message = f"Клип '{clip_name}' не найден" if clip_name else "Клип не найден"
        super().__init__(
            message,
            suggestion="Используйте list_media_pool_clips() чтобы увидеть доступные клипы"
        )


class BinNotFoundError(ResolveAPIError):
    """Raised when the specified bin/folder cannot be found."""
    
    def __init__(self, bin_name: str = None):
        message = f"Папка '{bin_name}' не найдена" if bin_name else "Папка не найдена"
        super().__init__(
            message,
            suggestion="Используйте list_media_pool_bins() или create_bin('имя')"
        )


class RenderError(ResolveAPIError):
    """Raised when a render operation fails."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message or "Ошибка рендеринга",
            suggestion="Проверьте настройки рендера и доступность выходной папки"
        )


class PageSwitchError(ResolveAPIError):
    """Raised when switching pages fails."""
    
    def __init__(self, page_name: str = None):
        message = f"Не удалось переключиться на страницу '{page_name}'" if page_name else "Ошибка переключения страницы"
        super().__init__(
            message,
            suggestion="Доступные страницы: media, cut, edit, fusion, color, fairlight, deliver"
        )


class ColorGradeError(ResolveAPIError):
    """Raised when color grading operations fail."""
    
    def __init__(self, message: str = None):
        super().__init__(
            message or "Ошибка цветокоррекции",
            suggestion="Убедитесь, что выбран клип в timeline и вы находитесь на странице Color"
        )


class MediaImportError(ResolveAPIError):
    """Raised when media import fails."""
    
    def __init__(self, file_path: str = None, reason: str = None):
        message = f"Не удалось импортировать '{file_path}'" if file_path else "Ошибка импорта медиа"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            suggestion="Проверьте путь к файлу и поддерживаемые форматы"
        )


# =====================
# Decorators
# =====================

def require_resolve(func: F) -> F:
    """Decorator that ensures DaVinci Resolve is connected.
    
    The decorated function must have 'resolve' as its first argument.
    
    Usage:
        @require_resolve
        def my_function(resolve, arg1, arg2):
            ...
    """
    @wraps(func)
    def wrapper(resolve, *args, **kwargs):
        if resolve is None:
            raise ResolveNotConnectedError()
        return func(resolve, *args, **kwargs)
    return wrapper


def require_project(func: F) -> F:
    """Decorator that ensures a project is currently open.
    
    The decorated function must have 'resolve' as its first argument.
    Also ensures resolve is connected.
    
    Usage:
        @require_project
        def my_function(resolve, arg1, arg2):
            ...
    """
    @wraps(func)
    def wrapper(resolve, *args, **kwargs):
        if resolve is None:
            raise ResolveNotConnectedError()
        
        pm = resolve.GetProjectManager()
        if pm is None:
            raise ResolveNotConnectedError("Не удалось получить Project Manager")
        
        project = pm.GetCurrentProject()
        if project is None:
            raise ProjectNotOpenError()
        
        return func(resolve, *args, **kwargs)
    return wrapper


def require_timeline(func: F) -> F:
    """Decorator that ensures a timeline is currently active.
    
    The decorated function must have 'resolve' as its first argument.
    Also ensures project is open.
    
    Usage:
        @require_timeline
        def my_function(resolve, arg1, arg2):
            ...
    """
    @wraps(func)
    def wrapper(resolve, *args, **kwargs):
        if resolve is None:
            raise ResolveNotConnectedError()
        
        pm = resolve.GetProjectManager()
        if pm is None:
            raise ResolveNotConnectedError("Не удалось получить Project Manager")
        
        project = pm.GetCurrentProject()
        if project is None:
            raise ProjectNotOpenError()
        
        timeline = project.GetCurrentTimeline()
        if timeline is None:
            raise NoCurrentTimelineError()
        
        return func(resolve, *args, **kwargs)
    return wrapper


def require_color_page(func: F) -> F:
    """Decorator that ensures we're on the Color page.
    
    The decorated function must have 'resolve' as its first argument.
    Automatically switches to Color page if needed.
    """
    @wraps(func)
    def wrapper(resolve, *args, **kwargs):
        if resolve is None:
            raise ResolveNotConnectedError()
        
        current_page = resolve.GetCurrentPage()
        if current_page != "color":
            logger.info("Switching to Color page for color operation")
            if not resolve.OpenPage("color"):
                raise PageSwitchError("color")
        
        return func(resolve, *args, **kwargs)
    return wrapper


def require_deliver_page(func: F) -> F:
    """Decorator that ensures we're on the Deliver page.
    
    The decorated function must have 'resolve' as its first argument.
    Automatically switches to Deliver page if needed.
    """
    @wraps(func)
    def wrapper(resolve, *args, **kwargs):
        if resolve is None:
            raise ResolveNotConnectedError()
        
        current_page = resolve.GetCurrentPage()
        if current_page != "deliver":
            logger.info("Switching to Deliver page for render operation")
            if not resolve.OpenPage("deliver"):
                raise PageSwitchError("deliver")
        
        return func(resolve, *args, **kwargs)
    return wrapper


def safe_api_call(default_return: Any = None, log_errors: bool = True):
    """Decorator for safe API calls with automatic error handling.
    
    Catches exceptions and returns a default value or error dict.
    
    Args:
        default_return: Value to return on error (if None, returns error dict)
        log_errors: Whether to log errors
        
    Usage:
        @safe_api_call(default_return=[])
        def my_function(resolve):
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ResolveAPIError as e:
                if log_errors:
                    logger.error(f"{func.__name__}: {e.message}")
                if default_return is not None:
                    return default_return
                return e.to_dict()
            except Exception as e:
                if log_errors:
                    logger.error(f"{func.__name__} failed: {str(e)}")
                if default_return is not None:
                    return default_return
                return {"error": str(e)}
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay_seconds: float = 0.5):
    """Decorator that retries a function on failure.
    
    Useful for operations that may fail due to timing issues.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Delay between retries
    """
    import time
    
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay_seconds)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
            raise last_exception
        return wrapper
    return decorator


# =====================
# Helper Functions
# =====================

def get_project_safe(resolve) -> Tuple[bool, Any, str]:
    """Safely get the current project with error message.
    
    Returns:
        Tuple of (success, project_or_none, message)
    """
    if resolve is None:
        return False, None, "DaVinci Resolve не подключен"
    
    pm = resolve.GetProjectManager()
    if pm is None:
        return False, None, "Не удалось получить Project Manager"
    
    project = pm.GetCurrentProject()
    if project is None:
        return False, None, "Проект не открыт"
    
    return True, project, "OK"


def get_timeline_safe(resolve) -> Tuple[bool, Any, str]:
    """Safely get the current timeline with error message.
    
    Returns:
        Tuple of (success, timeline_or_none, message)
    """
    success, project, message = get_project_safe(resolve)
    if not success:
        return False, None, message
    
    timeline = project.GetCurrentTimeline()
    if timeline is None:
        return False, None, "Нет активного timeline"
    
    return True, timeline, "OK"


def get_media_pool_safe(resolve) -> Tuple[bool, Any, str]:
    """Safely get the media pool with error message.
    
    Returns:
        Tuple of (success, media_pool_or_none, message)
    """
    success, project, message = get_project_safe(resolve)
    if not success:
        return False, None, message
    
    media_pool = project.GetMediaPool()
    if media_pool is None:
        return False, None, "Не удалось получить Media Pool"
    
    return True, media_pool, "OK"


def format_error_response(error: Union[Exception, str], 
                          suggestion: str = None,
                          context: dict = None) -> dict:
    """Format an error response for API return.
    
    Args:
        error: Exception or error message string
        suggestion: Optional suggestion for fixing the error
        context: Optional additional context
        
    Returns:
        Formatted error dictionary
    """
    if isinstance(error, ResolveAPIError):
        result = error.to_dict()
    else:
        result = {"error": str(error)}
        if suggestion:
            result["suggestion"] = suggestion
    
    if context:
        result["context"] = context
    
    return result


def validate_clip_name(resolve, clip_name: str) -> Tuple[bool, Any, str]:
    """Validate that a clip exists in the media pool.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Name of the clip to find
        
    Returns:
        Tuple of (found, clip_or_none, message)
    """
    success, media_pool, message = get_media_pool_safe(resolve)
    if not success:
        return False, None, message
    
    root_folder = media_pool.GetRootFolder()
    if root_folder is None:
        return False, None, "Не удалось получить корневую папку Media Pool"
    
    # Search recursively
    def find_clip(folder):
        for clip in folder.GetClipList():
            if clip.GetName() == clip_name:
                return clip
        for subfolder in folder.GetSubFolderList():
            result = find_clip(subfolder)
            if result:
                return result
        return None
    
    clip = find_clip(root_folder)
    if clip is None:
        return False, None, f"Клип '{clip_name}' не найден в Media Pool"
    
    return True, clip, "OK"
