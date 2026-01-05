# DaVinci Resolve MCP Server - API Reference

Comprehensive documentation of all available tools and resources.

---

## 📖 Table of Contents

1. [Transcription](#transcription)
2. [Timeline Operations](#timeline-operations)
3. [Media Pool](#media-pool)
4. [Project Management](#project-management)
5. [Smart Editing / AI](#smart-editing--ai)
6. [Color Page](#color-page)
7. [Delivery / Render](#delivery--render)

---

## Transcription

Audio transcription using Whisper AI.

### Tools

| Tool | Description | Arguments |
|------|-------------|-----------|
| `transcribe` | Transcribe audio/video file | `file_path`, `language`, `output_format` |
| `transcribe_clip` | Transcribe Media Pool clip | `clip_name`, `language`, `output_format` |
| `transcribe_clip_to_cache` | Transcribe and cache result | `clip_name`, `model_size`, `force_retranscribe` |
| `get_cached_transcription` | Read from cache | `clip_name` |
| `get_clip_transcription` | Auto-transcribe or load cache | `clip_name`, `model_size` |
| `transcribe_folder_tool` | Transcribe folder (Native AI) | `folder_name` |
| `transcribe_clip_tool` | Transcribe with Whisper | `clip_name`, `model_size` |

### Resources

| Resource | Description |
|----------|-------------|
| `whisper://status` | Whisper server status |

---

## Timeline Operations

Create and manage timelines.

### Tools

| Tool | Description | Arguments |
|------|-------------|-----------|
| `create_timeline` | Create new timeline | `name` |
| `create_empty_timeline` | Create with custom settings | `name`, `frame_rate`, `resolution_width`, `resolution_height`, etc. |
| `delete_timeline` | Delete timeline | `name` |
| `set_current_timeline` | Switch to timeline | `name` |
| `add_marker` | Add marker | `frame`, `color`, `note` |
| `append_clips_to_timeline` | Add clips to timeline | `clip_names`, `timeline_name` |
| `create_timeline_from_clips` | Create timeline with clips | `name`, `clip_names` |
| `create_trendy_timeline` | Create structured timeline | `edits`, `timeline_name` |
| `assemble_viral_reels` | Create vertical reels | `clip_name`, `segments` |
| `set_timeline_item_transform` | Set transform property | `item_id`, `property_name`, `value` |
| `set_timeline_item_crop` | Set crop property | `item_id`, `crop_type`, `value` |

### Resources

| Resource | Description |
|----------|-------------|
| `resolve://timelines` | List all timelines |
| `resolve://current-timeline` | Current timeline info |
| `resolve://timeline-tracks` | Track structure |
| `resolve://timeline-items` | All timeline items |
| `resolve://timeline-item/{id}` | Item properties |
| `resolve://timeline-clips` | Clips in timeline |

---

## Media Pool

Manage media files and organization.

### Tools

| Tool | Description | Arguments |
|------|-------------|-----------|
| `import_media` | Import file | `file_path` |
| `create_bin` | Create folder | `name` |
| `delete_media` | Delete clip | `clip_name` |
| `move_media_to_bin` | Move clip | `clip_name`, `bin_name` |
| `auto_sync_audio` | Sync audio | `clip_names`, `sync_method`, `append_mode`, `target_bin` |
| `unlink_clips` | Unlink clips | `clip_names` |
| `relink_clips` | Relink clips | `clip_names`, `media_paths`, `folder_path`, `recursive` |
| `create_sub_clip` | Create subclip | `clip_name`, `start_frame`, `end_frame`, `sub_clip_name`, `bin_name` |
| `add_clip_to_timeline` | Add to timeline | `clip_name`, `timeline_name` |
| `link_proxy_media` | Link proxy | `clip_name`, `proxy_file_path` |
| `unlink_proxy_media` | Unlink proxy | `clip_name` |
| `replace_clip` | Replace clip | `clip_name`, `replacement_path` |
| `transcribe_audio_native` | Native AI transcription | `clip_name`, `language` |
| `clear_transcription_native` | Clear transcription | `clip_name` |
| `export_folder` | Export to DRB | `folder_name`, `export_path`, `export_type` |
| `transcribe_folder_audio` | Transcribe folder audio | `folder_name`, `language` |
| `clear_folder_transcription_native` | Clear folder transcription | `folder_name` |
| `import_folder_from_drb` | Import folder from DRB | `path`, `source_bin_name` |
| `delete_folder` | Delete folder | `folder_name` |
| `get_folder_is_stale` | Check folder staleness | `folder_name` |

### Resources

| Resource | Description |
|----------|-------------|
| `resolve://media-pool-clips` | All clips |
| `resolve://media-pool-bins` | All folders |
| `resolve://media-pool-bin/{name}` | Folder contents |

---

## Project Management

Project settings and configuration.

### Tools

| Tool | Description | Arguments |
|------|-------------|-----------|
| `open_project` | Open project | `name` |
| `create_project` | Create project | `name` |
| `save_project` | Save current project | — |
| `set_project_property_tool` | Set property | `property_name`, `property_value` |
| `set_timeline_format_tool` | Set resolution/FPS | `width`, `height`, `frame_rate`, `interlaced` |
| `set_superscale_settings_tool` | Set SuperScale | `enabled`, `quality` |
| `set_color_science_mode_tool` | Set color mode | `mode` |
| `set_color_space_tool` | Set color space | `color_space`, `gamma` |
| `set_cache_mode` | Set cache mode | `mode` |
| `set_optimized_media_mode` | Set optimized media | `mode` |
| `set_proxy_mode` | Set proxy mode | `mode` |
| `set_proxy_quality` | Set proxy quality | `quality` |
| `set_cache_path` | Set cache path | `path_type`, `path` |
| `generate_optimized_media` | Generate optimized | `clip_names` |
| `delete_optimized_media` | Delete optimized | `clip_names` |

### Resources

| Resource | Description |
|----------|-------------|
| `resolve://projects` | All projects |
| `resolve://current-project` | Current project |
| `resolve://project/properties` | All properties |
| `resolve://project/property/{name}` | Specific property |
| `resolve://project/timeline-format` | Timeline format |
| `resolve://project/superscale` | SuperScale settings |
| `resolve://project/color-settings` | Color settings |
| `resolve://project/metadata` | Project metadata |
| `resolve://project/info` | Full project info |
| `resolve://cache/settings` | Cache settings |

---

## Smart Editing / AI

AI-powered editing automation.

### Tools

| Tool | Description | Arguments |
|------|-------------|-----------|
| `smart_jump_cut` | Remove silence | `clip_name`, `silence_threshold` |
| `viral_reels_factory` | Generate 9:16 reels | `clip_name` |
| `podcast_to_clips` | Convert podcast to clips | `clip_name`, `max_clips`, `min_duration`, `max_duration`, `content_style`, `create_timelines` |
| `analyze_content` | Analyze viral potential | `file_path`, `clip_name`, `content_style` |
| `find_viral_segments` | Find best moments | `clip_name`, `max_segments`, `min_duration`, `max_duration`, `language` |
| `create_viral_clips` | Create viral clips | `clip_name`, `segments`, `auto_detect`, `content_style`, `max_segments`, `timeline_prefix` |

---

## Color Page

Color grading operations.

### Tools

| Tool | Description | Arguments |
|------|-------------|-----------|
| `apply_lut` | Apply LUT | `lut_path`, `node_index` |
| `set_color_wheel_param` | Set wheel param | `wheel`, `param`, `value`, `node_index` |
| `add_node` | Add node | `node_type`, `label` |
| `copy_grade` | Copy grade | `source_clip_name`, `target_clip_name`, `mode` |
| `get_node_label` | Get node label | `node_index` |
| `get_node_lut` | Get node LUT | `node_index` |
| `grab_still` | Grab still | `still_album` |
| `delete_gallery_stills` | Delete stills | `album_name`, `still_labels` |
| `get_still_label` | Get still label | `still_index`, `album_name` |
| `set_still_label` | Set still label | `label`, `still_index`, `album_name` |

### Resources

| Resource | Description |
|----------|-------------|
| `resolve://color/current-node` | Current node info |
| `resolve://color/wheels/{index}` | Color wheel params |

---

## Delivery / Render

Rendering and export.

### Tools

| Tool | Description | Arguments |
|------|-------------|-----------|
| `add_to_render_queue` | Add to queue | `preset_name`, `timeline_name`, `use_in_out_range` |
| `start_render` | Start rendering | — |
| `clear_render_queue` | Clear queue | — |

### Resources

| Resource | Description |
|----------|-------------|
| `resolve://delivery/render-presets` | Available presets |
| `resolve://delivery/render-queue/status` | Queue status |

---

## Summary

> **Note**: This reference covers core tools only. For the complete list of **273 tools + 38 resources**, see [CAPABILITIES.md](../CAPABILITIES.md).

| Category | Tools (this doc) | Resources | Notes |
|----------|------------------|-----------|-------|
| Transcription | 7 | 1 | Whisper integration |
| Timeline | 11 | 6 | Core operations |
| Media Pool | 20 | 3 | Clip management |
| Project | 15 | 10 | Settings & lifecycle |
| Smart Editing | 6 | 0 | AI-powered |
| Color | 10 | 2 | Basic grading |
| Delivery | 3 | 2 | Render queue |
| **Documented Here** | **72** | **24** | **96 endpoints** |
| **Full Server** | **273** | **38** | **311 endpoints** |
