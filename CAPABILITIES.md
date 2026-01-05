# DaVinci Resolve MCP — Capabilities

Comprehensive list of all available MCP tools and resources.

## Quick Stats

| Module | Tools | Resources | Description |
|--------|-------|-----------|-------------|
| Navigation | 4 | 2 | Page switching, system info |
| Project | 49 | 12 | Lifecycle, settings, presets, cloud |
| MediaStorage | 6 | 1 | Storage browsing, add to pool |
| Media | 42 | 10 | MediaPool clips, metadata, mattes |
| Timeline | 72 | 7 | Tracks, items, markers, stereo, cache |
| Fusion | 11 | 2 | Compositions, Text+, templates |
| Color | 38 | 0 | Node graph, gallery, color groups |
| Fairlight | 13 | 0 | Audio, voice isolation |
| Delivery | 14 | 4 | Render queue, quick export |
| **Total** | **273** | **38** | **311 endpoints** |


---

## Navigation Tools

| Tool | Description |
|------|-------------|
| `open_page` | Switch to page (media/cut/edit/fusion/color/fairlight/deliver) |
| `get_current_page` | Get currently displayed page |
| `get_system_info` | Get Resolve product and version |
| `quit_resolve` | Close DaVinci Resolve |

---

## Project Management

### Lifecycle
| Tool | Description |
|------|-------------|
| `list_projects` | List all projects in database |
| `get_current_project_name` | Get current project name |
| `open_project` | Open project by name |
| `create_project` | Create new project |
| `save_project` | Save current project |
| `delete_project` | Delete project |
| `close_project` | Close current project |
| `rename_project` | Rename project |
| `export_project` | Export project (.drp) |
| `import_project` | Import project file |
| `archive_project` | Create project archive |
| `restore_project` | Restore from archive |
| `get_project_unique_id` | Get project UUID |

### Settings
| Tool | Description |
|------|-------------|
| `get_project_properties` | Get all project properties |
| `set_project_property_tool` | Set project property |
| `get_timeline_format` | Get resolution/framerate |
| `set_timeline_format_tool` | Set resolution/framerate |
| `get_superscale_settings` | Get SuperScale config |
| `set_superscale_settings_tool` | Set SuperScale |
| `get_color_settings_resource` | Get color science |
| `set_color_science_mode_tool` | Set color science mode |
| `set_color_space_tool` | Set color space/gamma |
| `get_cache_settings` | Get cache config |
| `set_cache_mode` | Set cache mode |
| `set_optimized_media_mode` | Set optimized media |
| `set_proxy_mode` | Set proxy mode |
| `generate_optimized_media` | Generate optimized media |
| `delete_optimized_media` | Delete optimized media |

### Database
| Tool | Description |
|------|-------------|
| `list_database_folders` | List DB folders |
| `create_database_folder` | Create DB folder |
| `delete_database_folder` | Delete DB folder |
| `open_database_folder` | Open DB folder |
| `goto_root_folder` | Go to DB root |
| `goto_parent_folder` | Go to parent folder |
| `get_database_list` | List databases |
| `set_current_database` | Switch database |

---

## MediaStorage

Browse mounted storage volumes and add files directly to MediaPool.

### Browse Tools
| Tool | Description |
|------|-------------|
| `list_mounted_volumes` | List all mounted volumes |
| `list_storage_folders` | List subfolders in path |
| `list_storage_files` | List media files in path |
| `reveal_in_storage` | Reveal path in Media Storage browser |

### Add to Pool Tools
| Tool | Description |
|------|-------------|
| `add_from_storage` | Add files to current MediaPool folder |
| `add_from_storage_with_range` | Add with specific in/out frames |
| `add_timeline_mattes` | Add timeline matte files |

### Resources
| Resource | Description |
|----------|-------------|
| `resolve://media-storage/volumes` | All mounted volumes |

---

## MediaPool

### Clip Management
| Tool | Description |
|------|-------------|
| `list_clips` / `list_media_pool_clips` | List all clips |
| `import_media` | Import media file |
| `create_bin` | Create new bin |
| `add_clip_to_timeline` | Append clip to timeline |
| `delete_media` | Delete clip |
| `move_media_to_bin` | Move clip to bin |
| `replace_clip` | Replace clip with file |
| `unlink_clips` | Unlink clips |
| `relink_clips` | Relink clips |
| `create_sub_clip` | Create subclip |

### Metadata
| Tool | Description |
|------|-------------|
| `get_clip_metadata` | Get all metadata |
| `set_clip_metadata` | Set metadata dict |
| `get_clip_properties` | Get clip properties |
| `set_clip_property` | Set clip property |
| `get_clip_unique_id` | Get clip UUID |
| `rename_clip` | Rename clip |

### Markers/Flags
| Tool | Description |
|------|-------------|
| `add_clip_marker` | Add marker to clip |
| `get_clip_markers` | Get clip markers |
| `delete_clip_marker` | Delete marker |
| `add_clip_flag` | Add flag |
| `get_clip_flags` | Get flags |
| `clear_clip_flags` | Clear flags |
| `get_clip_color` | Get clip color |
| `set_clip_color` | Set clip color |
| `clear_clip_color` | Clear clip color |

### Mark In/Out
| Tool | Description |
|------|-------------|
| `get_clip_mark_in_out` | Get mark in/out |
| `set_clip_mark_in_out` | Set mark in/out |
| `clear_clip_mark_in_out` | Clear marks |

### Proxy/Sync
| Tool | Description |
|------|-------------|
| `link_proxy_media` | Link proxy |
| `unlink_proxy_media` | Unlink proxy |
| `auto_sync_audio` | Sync audio |
| `transcribe_audio_native` | Transcribe audio |
| `clear_transcription_native` | Clear transcription |
| `export_folder` | Export folder |
| `transcribe_folder_audio` | Transcribe folder |

---

## Timeline

### Management
| Tool | Description |
|------|-------------|
| `list_timelines` | List all timelines |
| `get_current_timeline` | Get current timeline info |
| `create_timeline` | Create timeline |
| `create_empty_timeline` | Create with settings |
| `delete_timeline` | Delete timeline |
| `set_current_timeline` | Switch timeline |
| `duplicate_timeline` | Duplicate timeline |
| `rename_timeline` | Rename timeline |
| `get_timeline_id` | Get timeline UUID |

### Tracks
| Tool | Description |
|------|-------------|
| `get_timeline_tracks` | Get track structure |
| `add_track` | Add track |
| `delete_track` | Delete track |
| `get_track_name` | Get track name |
| `set_track_name` | Set track name |
| `set_track_enabled` | Enable/disable track |
| `set_track_locked` | Lock/unlock track |
| `get_track_status` | Get track status |

### Timecode
| Tool | Description |
|------|-------------|
| `get_current_timecode` | Get playhead position |
| `set_current_timecode` | Set playhead position |

### Clips
| Tool | Description |
|------|-------------|
| `list_timeline_clips` | List clips in timeline |
| `append_clips_to_timeline` | Append clips |
| `create_timeline_from_clips` | Create from clips |
| `get_timeline_items` | Get all items |
| `get_timeline_item_properties` | Get item properties |
| `set_timeline_item_transform` | Set transform |
| `set_timeline_item_crop` | Set crop |

### Generators/Titles
| Tool | Description |
|------|-------------|
| `insert_generator` | Insert generator |
| `insert_title` | Insert title |
| `insert_fusion_title` | Insert Fusion title |
| `create_compound_clip` | Create compound |
| `create_fusion_clip` | Create Fusion clip |
| `detect_scene_cuts` | Detect scene cuts |

### Export/Import
| Tool | Description |
|------|-------------|
| `export_timeline` | Export (EDL/XML/AAF/FCPXML) |
| `import_timeline_from_file` | Import timeline |

### Markers
| Tool | Description |
|------|-------------|
| `add_marker` | Add timeline marker |
| `get_timeline_markers` | Get markers |
| `delete_timeline_markers` | Delete markers |

### TimelineItem Extended
| Tool | Description |
|------|-------------|
| `get_timeline_item_property` | Get item property |
| `set_timeline_item_property` | Set item property |
| `get_timeline_item_info` | Get detailed info |
| `set_timeline_item_enabled` | Enable/disable item |
| `add_color_version` | Add color version |
| `get_color_versions` | Get versions |
| `load_color_version` | Load version |
| `stabilize_clip` | Stabilize item |
| `smart_reframe_clip` | Smart Reframe |
| `create_magic_mask` | Create Magic Mask |
| `add_timeline_item_marker` | Add item marker |
| `get_timeline_item_markers` | Get item markers |
| `set_timeline_item_color` | Set item color |
| `add_timeline_item_flag` | Add item flag |
| `set_color_output_cache` | Set color cache |
| `copy_grades` | Copy grades |
| `get_linked_items` | Get linked items |

### Timeline Extensions (Phase 1)
| Tool | Description |
|------|-------------|
| `delete_timeline_clips` | Delete clips from timeline |
| `get_timeline_setting` | Get timeline setting |
| `set_timeline_setting` | Set timeline setting |
| `get_current_video_item` | Get item at playhead |
| `create_subtitles_from_audio` | Auto-generate subtitles |
| `get_timeline_bounds` | Get start/end frames |
| `set_timeline_start_timecode` | Set start timecode |

### TimelineItem Extensions (Phase 1.5)
| Tool | Description |
|------|-------------|
| `get_timeline_item_duration` | Get item duration in frames |
| `get_timeline_item_start_end` | Get start/end position |
| `get_timeline_item_media_pool_item` | Get linked MediaPoolItem |
| `export_timeline_item_lut` | Export LUT from color grade |
| `set_cdl_values` | Set CDL (slope/offset/power/sat) |
| `get_timeline_item_node_graph` | Get node graph info |

---

## Fusion Page

Visual effects and compositing tools.

### Composition Tools
| Tool | Description |
|------|-------------|
| `get_fusion_composition` | Get Fusion comp info |
| `create_fusion_clip_tool` | Convert to Fusion clip |
| `list_fusion_templates_tool` | List templates/generators |
| `get_fusion_nodes` | Get nodes in current comp |

### Text and Graphics
| Tool | Description |
|------|-------------|
| `add_text_plus_node` | Add Text+ node |
| `create_lower_third_tool` | Create lower third template |
| `insert_fusion_generator` | Insert generator |
| `insert_fusion_title` | Insert title |

### Import/Export
| Tool | Description |
|------|-------------|
| `export_fusion_composition` | Export comp as .setting |
| `import_fusion_composition` | Import .setting file |

### Resources
| Resource | Description |
|----------|-------------|
| `resolve://fusion/templates` | All Fusion templates |
| `resolve://fusion/current-comp` | Current composition info |

---

## Color Page

### Nodes
| Tool | Description |
|------|-------------|
| `get_current_color_node` | Get current node info |
| `get_color_wheel_params` | Get color wheel params |
| `set_color_wheel_param` | Set wheel param |
| `apply_lut` | Apply LUT |
| `add_node` | Add node (serial/parallel/layer) |
| `copy_grade_tool` | Copy grade |
| `get_node_graph_info` | Get node graph |
| `set_node_lut` | Set LUT on node |
| `set_node_enabled` | Enable/disable node |
| `reset_all_grades` | Reset all grades |

### Gallery
| Tool | Description |
|------|-------------|
| `grab_still` | Grab still |
| `get_gallery_albums` | Get albums |
| `create_still_album` | Create album |
| `get_stills_in_album` | Get stills |
| `export_stills` | Export stills |
| `import_stills` | Import stills |

---

## Fairlight (Audio)

### Tracks
| Tool | Description |
|------|-------------|
| `get_audio_tracks` | Get audio tracks |
| `add_audio_track_fairlight` | Add audio track |
| `delete_audio_track_fairlight` | Delete track |
| `set_audio_track_enabled` | Enable/mute track |
| `set_audio_track_volume` | Set volume |

### Analysis
| Tool | Description |
|------|-------------|
| `get_audio_clip_info` | Get clip info |
| `analyze_audio_levels` | Analyze levels |

### Voice Isolation
| Tool | Description |
|------|-------------|
| `apply_voice_isolation` | Apply voice isolation |
| `get_voice_isolation_state` | Get VI state |
| `set_voice_isolation_state` | Set VI state |
| `get_audio_normalization_guide` | Normalization guide |
| `get_timeline_item_audio_mapping` | Get audio mapping |

---

## Delivery

### Queue
| Tool | Description |
|------|-------------|
| `get_render_presets` | Get presets |
| `add_to_render_queue` | Add to queue |
| `add_render_job` | Add job (robust) |
| `start_render` | Start render |
| `stop_render` | Stop render |
| `get_render_queue_status` | Get queue status |
| `delete_render_job` | Delete job |
| `clear_render_queue` | Clear queue |

### Settings
| Tool | Description |
|------|-------------|
| `get_render_formats` | Get formats/codecs |
| `set_render_settings` | Apply settings |
| `get_current_render_mode` | Get render mode |
| `load_render_preset` | Load preset |
| `save_render_preset` | Save preset |

### Delivery Extensions (Phase 1)
| Tool | Description |
|------|-------------|
| `is_rendering_in_progress` | Check if rendering |
| `set_current_render_format` | Set format/codec |
| `get_current_render_format` | Get current format/codec |
| `set_render_mode` | Set render mode |
| `export_current_frame_as_still` | Export frame as image |

### Quick Export (Phase 4.9)
| Tool | Description |
|------|-------------|
| `get_render_resolutions` | Get available resolutions |
| `get_quick_export_presets` | Get quick export presets |
| `render_with_quick_export` | Render with quick export to path |
| `quick_export` | Start quick export |

---

## Cloud Projects (Phase 4.10)

| Tool | Description |
|------|-------------|
| `create_cloud_project` | Create cloud project |
| `load_cloud_project` | Load cloud project |
| `import_cloud_project` | Import project to cloud |
| `restore_cloud_project` | Restore cloud project |

---

## Phase 4 Additions

### Timeline Extensions (4.1-4.2)
| Tool | Description |
|------|-------------|
| `add_marker_with_custom_data` | Add marker with custom data |
| `get_timeline_marker_by_custom_data` | Find marker by custom data |
| `update_timeline_marker_custom_data` | Update marker custom data |
| `set_clips_linked` | Link/unlink clips |
| `grab_timeline_still` | Grab still from timeline |
| `grab_all_timeline_stills` | Grab stills from all clips |
| `convert_timeline_to_stereo` | Convert to stereo 3D |
| `get_timeline_item_left_offset` | Get left handle |
| `get_timeline_item_right_offset` | Get right handle |
| `add_take` | Add take to selector |
| `get_takes_count` | Get take count |
| `select_take_by_index` | Select take |
| `finalize_take` | Finalize current take |
| `regenerate_magic_mask` | Regenerate Magic Mask |
| `update_sidecar` | Update BRAW/R3D sidecar |

### Media Extensions (4.3-4.4, 4.6)
| Tool | Description |
|------|-------------|
| `get_third_party_metadata` | Get third-party metadata |
| `set_third_party_metadata` | Set third-party metadata |
| `link_full_resolution_media` | Link full-res media |
| `replace_clip_preserve_sub_clip` | Replace preserving subclip |
| `monitor_growing_file` | Monitor growing file |
| `create_stereo_clip` | Create stereo clip |
| `get_clip_matte_list` | Get clip mattes |
| `get_timeline_matte_list` | Get timeline mattes |
| `delete_clip_mattes` | Delete clip mattes |
| `get_folder_is_stale` | Check folder staleness |
| `get_folder_unique_id` | Get folder ID |
| `export_folder_to_drb` | Export folder as DRB |
| `import_folder_from_drb` | Import folder from DRB |
| `delete_folder` | Delete folder |

### Color Group Extensions (4.7-4.8)
| Tool | Description |
|------|-------------|
| `get_color_groups` | Get color groups |
| `get_color_group_clips_in_timeline` | Get clips in color group |
| `get_pre_clip_node_graph` | Get pre-clip node graph |
| `get_post_clip_node_graph` | Get post-clip node graph |
| `assign_to_color_group` | Assign clip to group |
| `remove_from_color_group` | Remove from group |
| `reset_all_node_colors` | Reset node colors |
| `delete_stills_from_album` | Delete stills |
| `get_still_label` | Get still label |
| `set_still_label` | Set still label |
| `get_node_label` | Get node label |
| `get_node_lut` | Get node LUT |
| `delete_gallery_stills` | Delete stills (alias) |

---

## Requirements

- DaVinci Resolve 18.0+ (some features require Studio)
- Python 3.10+
- MCP-compatible client (Claude Desktop, Cursor, etc.)

## Usage

```bash
# Start MCP server
python -m src.resolve_mcp_server
```
