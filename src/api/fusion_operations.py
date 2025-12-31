#!/usr/bin/env python3
"""
DaVinci Resolve Fusion Page Operations

Provides visual effects and compositing functionality:
- Fusion composition access
- Node creation and manipulation
- Text and title effects
- Templates and presets
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("davinci-resolve-mcp.fusion")


def _get_fusion_context(resolve) -> Tuple[bool, Any, Any, Any, str]:
    """Get Fusion page context (project, timeline, clip).
    
    Returns:
        Tuple of (success, project, timeline, current_clip, error_message)
    """
    if not resolve:
        return False, None, None, None, "DaVinci Resolve не подключен"
    
    pm = resolve.GetProjectManager()
    if not pm:
        return False, None, None, None, "Не удалось получить Project Manager"
    
    project = pm.GetCurrentProject()
    if not project:
        return False, None, None, None, "Проект не открыт"
    
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return False, None, None, None, "Нет активного timeline"
    
    return True, project, timeline, None, "OK"


def get_fusion_comp(resolve, clip_name: str = None) -> Dict[str, Any]:
    """Get Fusion composition for a timeline clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Clip name to get composition for (uses current if None)
        
    Returns:
        Dictionary with Fusion composition information
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    # Switch to Fusion page
    if resolve.GetCurrentPage() != "fusion":
        resolve.OpenPage("fusion")
    
    try:
        # Find the clip
        video_tracks = timeline.GetTrackCount("video")
        target_clip = None
        
        for i in range(1, video_tracks + 1):
            items = timeline.GetItemListInTrack("video", i)
            if items:
                for item in items:
                    if clip_name:
                        if hasattr(item, 'GetName') and item.GetName() == clip_name:
                            target_clip = item
                            break
                    else:
                        # Use first clip found
                        target_clip = item
                        break
            if target_clip:
                break
        
        if not target_clip:
            return {"error": f"Клип не найден" + (f": '{clip_name}'" if clip_name else "")}
        
        # Get Fusion composition
        fusion_comp = target_clip.GetFusionCompByIndex(1)
        
        result = {
            "clip_name": target_clip.GetName() if hasattr(target_clip, 'GetName') else "Unknown",
            "has_fusion_comp": fusion_comp is not None
        }
        
        if fusion_comp:
            # Get composition details
            try:
                result["comp_name"] = fusion_comp.GetName() if hasattr(fusion_comp, 'GetName') else "Composition"
                
                # Count Fusion compositions on this clip
                comp_count = target_clip.GetFusionCompCount()
                result["comp_count"] = comp_count
                
                # Try to get nodes
                nodes = fusion_comp.GetToolList()
                if nodes:
                    result["node_count"] = len(nodes)
                    result["nodes"] = []
                    for node_id, node in nodes.items():
                        node_info = {
                            "id": node_id,
                            "name": node.GetAttrs()["TOOLS_Name"] if hasattr(node, 'GetAttrs') else str(node_id)
                        }
                        result["nodes"].append(node_info)
            except Exception as e:
                logger.warning(f"Could not get full comp details: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting Fusion comp: {e}")
        return {"error": f"Ошибка получения Fusion композиции: {str(e)}"}


def create_fusion_clip(resolve, clip_name: str = None) -> Dict[str, Any]:
    """Create a Fusion clip from a timeline clip.
    
    Args:
        resolve: DaVinci Resolve instance
        clip_name: Clip to convert (uses current selection if None)
        
    Returns:
        Status dictionary
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    try:
        video_tracks = timeline.GetTrackCount("video")
        target_clip = None
        
        for i in range(1, video_tracks + 1):
            items = timeline.GetItemListInTrack("video", i)
            if items:
                for item in items:
                    if clip_name is None or (hasattr(item, 'GetName') and item.GetName() == clip_name):
                        target_clip = item
                        break
            if target_clip:
                break
        
        if not target_clip:
            return {"error": "Клип не найден"}
        
        # Add Fusion composition
        result = target_clip.AddFusionComp()
        
        if result:
            return {
                "success": True,
                "clip_name": target_clip.GetName() if hasattr(target_clip, 'GetName') else "Unknown",
                "comp_count": target_clip.GetFusionCompCount()
            }
        else:
            return {"error": "Не удалось создать Fusion композицию"}
            
    except Exception as e:
        logger.error(f"Error creating Fusion clip: {e}")
        return {"error": f"Ошибка создания Fusion клипа: {str(e)}"}


def add_text_plus(resolve, text: str, 
                  font: str = "Arial",
                  size: float = 0.1,
                  position: Tuple[float, float] = (0.5, 0.5),
                  color: Tuple[float, float, float] = (1.0, 1.0, 1.0)) -> Dict[str, Any]:
    """Add Text+ node to Fusion composition.
    
    Args:
        resolve: DaVinci Resolve instance
        text: Text content
        font: Font family name
        size: Text size (0.0-1.0 relative to frame)
        position: (x, y) position, 0.5 = center
        color: RGB color values (0.0-1.0)
        
    Returns:
        Status dictionary
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    # Switch to Fusion page
    if resolve.GetCurrentPage() != "fusion":
        resolve.OpenPage("fusion")
    
    try:
        # Get current clip
        video_tracks = timeline.GetTrackCount("video")
        target_clip = None
        
        for i in range(1, video_tracks + 1):
            items = timeline.GetItemListInTrack("video", i)
            if items and len(items) > 0:
                target_clip = items[0]
                break
        
        if not target_clip:
            return {"error": "Нет клипов в timeline"}
        
        # Get or create Fusion comp
        fusion_comp = target_clip.GetFusionCompByIndex(1)
        if not fusion_comp:
            target_clip.AddFusionComp()
            fusion_comp = target_clip.GetFusionCompByIndex(1)
        
        if not fusion_comp:
            return {"error": "Не удалось получить Fusion композицию"}
        
        # Create Text+ node
        # Note: Direct node creation API is limited
        return {
            "note": "Прямое создание Text+ через API ограничено",
            "instructions": [
                "1. Выберите клип и откройте Fusion page",
                "2. В Effects Library найдите 'Text+'",
                "3. Добавьте Text+ между MediaIn и MediaOut",
                f"4. Введите текст: {text}",
                f"5. Установите шрифт: {font}",
                f"6. Размер: {size}",
                f"7. Позиция: {position}"
            ],
            "clip": target_clip.GetName() if hasattr(target_clip, 'GetName') else "Unknown",
            "has_fusion_comp": fusion_comp is not None
        }
        
    except Exception as e:
        logger.error(f"Error adding Text+: {e}")
        return {"error": f"Ошибка добавления текста: {str(e)}"}


def create_lower_third(resolve, 
                       name: str,
                       title: str,
                       subtitle: str = "",
                       style: str = "minimal") -> Dict[str, Any]:
    """Create a lower third graphic.
    
    Args:
        resolve: DaVinci Resolve instance
        name: Name for the Fusion composition
        title: Main title text
        subtitle: Secondary text
        style: Visual style ('minimal', 'corporate', 'news')
        
    Returns:
        Instructions dictionary
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    style_descriptions = {
        "minimal": "Простой текст с мягкой тенью",
        "corporate": "Текст с цветной плашкой",
        "news": "Двухстрочный стиль новостей"
    }
    
    return {
        "type": "lower_third",
        "name": name,
        "title": title,
        "subtitle": subtitle,
        "style": style,
        "style_description": style_descriptions.get(style, "Custom style"),
        "instructions": [
            "1. Effects Library → Titles → Lower Thirds",
            "2. Выберите подходящий шаблон",
            "3. Перетащите на timeline",
            f"4. Отредактируйте: Title = '{title}'",
            f"5. Подзаголовок: '{subtitle}'" if subtitle else "5. Подзаголовок пуст",
            "6. Настройте цвета и анимацию в Inspector"
        ]
    }


def list_fusion_templates(resolve) -> Dict[str, Any]:
    """List available Fusion templates and generators.
    
    Args:
        resolve: DaVinci Resolve instance
        
    Returns:
        Dictionary with template categories
    """
    success, project, _, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    # These are standard categories in DaVinci Resolve
    return {
        "categories": {
            "generators": [
                "Solid Color",
                "10 Point Garbage Matte",
                "Grey Scale Gradient",
                "Linear Gradient",
                "Four Corner Gradient",
                "Radial Gradient"
            ],
            "titles": [
                "Text",
                "Text+",
                "Scroll",
                "Fusion Title"
            ],
            "effects": [
                "Adjustment Clip",
                "Fusion Composition"
            ],
            "transitions": [
                "Fusion Transition"
            ]
        },
        "custom_templates_path": "Effects Library → Toolbox → Templates",
        "note": "Для создания кастомных шаблонов сохраните Fusion композицию как .setting файл"
    }


def insert_generator(resolve, 
                     generator_name: str,
                     duration_frames: int = 150,
                     track_index: int = 1) -> Dict[str, Any]:
    """Insert a generator into the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        generator_name: Name of the generator
        duration_frames: Duration in frames
        track_index: Video track to insert on
        
    Returns:
        Status dictionary
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    try:
        # Get available generators
        media_pool = project.GetMediaPool()
        
        # Try to insert generator
        result = timeline.InsertGeneratorIntoTimeline(generator_name)
        
        if result:
            return {
                "success": True,
                "generator": generator_name,
                "message": f"Generator '{generator_name}' добавлен в timeline"
            }
        else:
            return {
                "error": f"Не удалось вставить generator '{generator_name}'",
                "available_generators": [
                    "Solid Color",
                    "Grey Scale Gradient", 
                    "Linear Gradient",
                    "Four Corner Gradient",
                    "Radial Gradient"
                ]
            }
            
    except Exception as e:
        logger.error(f"Error inserting generator: {e}")
        return {"error": f"Ошибка вставки generator: {str(e)}"}


def insert_title(resolve, title_name: str = "Text+") -> Dict[str, Any]:
    """Insert a title template into the timeline.
    
    Args:
        resolve: DaVinci Resolve instance
        title_name: Name of the title template
        
    Returns:
        Status dictionary
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    try:
        result = timeline.InsertFusionTitleIntoTimeline(title_name)
        
        if result:
            return {
                "success": True,
                "title": title_name,
                "message": f"Title '{title_name}' добавлен в timeline",
                "next_steps": [
                    "Выберите title на timeline",
                    "Откройте Inspector для редактирования текста",
                    "Используйте Fusion page для продвинутой настройки"
                ]
            }
        else:
            return {
                "error": f"Не удалось вставить title '{title_name}'",
                "available_titles": ["Text", "Text+", "Scroll"]
            }
            
    except Exception as e:
        logger.error(f"Error inserting title: {e}")
        return {"error": f"Ошибка вставки title: {str(e)}"}


def get_fusion_node_list(resolve) -> Dict[str, Any]:
    """Get list of nodes in the current Fusion composition.
    
    Args:
        resolve: DaVinci Resolve instance
        
    Returns:
        Dictionary with node information
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    # Switch to Fusion page
    if resolve.GetCurrentPage() != "fusion":
        resolve.OpenPage("fusion")
    
    try:
        # Get current clip
        video_tracks = timeline.GetTrackCount("video")
        target_clip = None
        
        for i in range(1, video_tracks + 1):
            items = timeline.GetItemListInTrack("video", i)
            if items and len(items) > 0:
                # Find first clip with Fusion comp
                for item in items:
                    if item.GetFusionCompCount() > 0:
                        target_clip = item
                        break
            if target_clip:
                break
        
        if not target_clip:
            return {
                "error": "Не найдено клипов с Fusion композициями",
                "suggestion": "Сначала создайте Fusion Clip с помощью create_fusion_clip()"
            }
        
        fusion_comp = target_clip.GetFusionCompByIndex(1)
        if not fusion_comp:
            return {"error": "Не удалось открыть Fusion композицию"}
        
        # Get all tools/nodes
        tools = fusion_comp.GetToolList()
        nodes = []
        
        if tools:
            for tool_id, tool in tools.items():
                node_info = {"id": tool_id}
                try:
                    attrs = tool.GetAttrs()
                    node_info["name"] = attrs.get("TOOLS_Name", str(tool_id))
                    node_info["type"] = attrs.get("TOOLS_RegID", "Unknown")
                except:
                    node_info["name"] = str(tool_id)
                    node_info["type"] = "Unknown"
                nodes.append(node_info)
        
        return {
            "clip_name": target_clip.GetName() if hasattr(target_clip, 'GetName') else "Unknown",
            "comp_count": target_clip.GetFusionCompCount(),
            "nodes": nodes,
            "node_count": len(nodes)
        }
        
    except Exception as e:
        logger.error(f"Error getting Fusion nodes: {e}")
        return {"error": f"Ошибка получения узлов: {str(e)}"}


def export_fusion_comp(resolve, output_path: str) -> Dict[str, Any]:
    """Export current Fusion composition as a .setting file.
    
    Args:
        resolve: DaVinci Resolve instance
        output_path: Path to save the .setting file
        
    Returns:
        Status dictionary
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    try:
        video_tracks = timeline.GetTrackCount("video")
        target_clip = None
        
        for i in range(1, video_tracks + 1):
            items = timeline.GetItemListInTrack("video", i)
            if items:
                for item in items:
                    if item.GetFusionCompCount() > 0:
                        target_clip = item
                        break
            if target_clip:
                break
        
        if not target_clip:
            return {"error": "Не найдено клипов с Fusion композициями"}
        
        # Export
        result = target_clip.ExportFusionComp(output_path, 1)  # Export first comp
        
        if result:
            return {
                "success": True,
                "path": output_path,
                "clip": target_clip.GetName() if hasattr(target_clip, 'GetName') else "Unknown"
            }
        else:
            return {"error": "Не удалось экспортировать Fusion композицию"}
            
    except Exception as e:
        logger.error(f"Error exporting Fusion comp: {e}")
        return {"error": f"Ошибка экспорта: {str(e)}"}


def import_fusion_comp(resolve, setting_path: str, clip_name: str = None) -> Dict[str, Any]:
    """Import a .setting file as Fusion composition.
    
    Args:
        resolve: DaVinci Resolve instance
        setting_path: Path to the .setting file
        clip_name: Clip to apply to (uses first clip if None)
        
    Returns:
        Status dictionary
    """
    success, project, timeline, _, msg = _get_fusion_context(resolve)
    if not success:
        return {"error": msg}
    
    import os
    if not os.path.exists(setting_path):
        return {"error": f"Файл не найден: {setting_path}"}
    
    try:
        video_tracks = timeline.GetTrackCount("video")
        target_clip = None
        
        for i in range(1, video_tracks + 1):
            items = timeline.GetItemListInTrack("video", i)
            if items:
                for item in items:
                    if clip_name is None or (hasattr(item, 'GetName') and item.GetName() == clip_name):
                        target_clip = item
                        break
            if target_clip:
                break
        
        if not target_clip:
            return {"error": "Клип не найден"}
        
        # Import
        result = target_clip.ImportFusionComp(setting_path)
        
        if result:
            return {
                "success": True,
                "path": setting_path,
                "clip": target_clip.GetName() if hasattr(target_clip, 'GetName') else "Unknown",
                "comp_count": target_clip.GetFusionCompCount()
            }
        else:
            return {"error": "Не удалось импортировать Fusion композицию"}
            
    except Exception as e:
        logger.error(f"Error importing Fusion comp: {e}")
        return {"error": f"Ошибка импорта: {str(e)}"}
