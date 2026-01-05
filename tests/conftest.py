"""
Pytest configuration and fixtures for DaVinci Resolve MCP tests.

Provides mock objects for testing without requiring DaVinci Resolve to be running.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock
from typing import Dict, List, Any


# =====================
# Mock DaVinci Resolve
# =====================

class MockMediaPoolItem:
    """Mock Media Pool Item (clip)."""
    
    def __init__(self, name: str, properties: Dict = None):
        self._name = name
        self._properties = properties or {
            "FPS": "24",
            "Duration": "00:01:00:00",
            "Start TC": "01:00:00:00",
            "File Path": f"/media/{name}.mp4"
        }
        self._markers = {}
    
    def GetName(self) -> str:
        return self._name
    
    def GetClipProperty(self, prop: str = None) -> Any:
        if prop:
            return self._properties.get(prop, "")
        return self._properties
    
    def SetClipProperty(self, prop: str, value: Any) -> bool:
        self._properties[prop] = value
        return True
    
    def GetMarkers(self) -> Dict:
        return self._markers
    
    def AddMarker(self, frame: int, color: str, name: str, note: str = "") -> bool:
        self._markers[frame] = {"color": color, "name": name, "note": note}
        return True


class MockFolder:
    """Mock Media Pool Folder."""
    
    def __init__(self, name: str):
        self._name = name
        self._clips: List[MockMediaPoolItem] = []
        self._subfolders: List['MockFolder'] = []
    
    def GetName(self) -> str:
        return self._name
        
    def GetIsFolderStale(self) -> bool:
        return False
    
    def Export(self, path: str) -> bool:
        return True
    
    def GetClipList(self) -> List[MockMediaPoolItem]:
        return self._clips
    
    def GetSubFolderList(self) -> List['MockFolder']:
        return self._subfolders
    
    def AddClip(self, clip: MockMediaPoolItem):
        self._clips.append(clip)
    
    def AddSubFolder(self, folder: 'MockFolder'):
        self._subfolders.append(folder)

    def ClearTranscription(self) -> bool:
        return True


class MockMediaPool:
    """Mock Media Pool."""
    
    def __init__(self, project=None):
        self._root_folder = MockFolder("Master")
        self._current_folder = self._root_folder
        self._project = project
    
    def GetRootFolder(self) -> MockFolder:
        return self._root_folder
    
    def GetCurrentFolder(self) -> MockFolder:
        return self._current_folder
    
    def SetCurrentFolder(self, folder: MockFolder) -> bool:
        self._current_folder = folder
        return True
    
    def AddSubFolder(self, parent: MockFolder, name: str) -> MockFolder:
        new_folder = MockFolder(name)
        parent.AddSubFolder(new_folder)
        return new_folder
    
    def ImportMedia(self, paths: List[str]) -> List[MockMediaPoolItem]:
        clips = []
        for path in paths:
            name = path.split("/")[-1].split("\\")[-1]
            clip = MockMediaPoolItem(name)
            self._current_folder.AddClip(clip)
            clips.append(clip)
        return clips
    
    def AppendToTimeline(self, clips: List) -> List:
        return clips  # Simplified
    
    def ImportFolderFromFile(self, path: str, source_bin_name: str = None) -> MockFolder:
        folder_name = source_bin_name if source_bin_name else path.split("/")[-1].split(".")[0]
        return self.AddSubFolder(self._root_folder, folder_name)
    
    def DeleteFolders(self, folders: List[MockFolder]) -> bool:
        for folder in folders:
            # Simplified deletion from root or subfolders
            if folder in self._root_folder._subfolders:
                self._root_folder._subfolders.remove(folder)
        return True
    
    def CreateEmptyTimeline(self, name: str) -> 'MockTimeline':
        timeline = MockTimeline(name)
        
        # Inherit settings if linked to a project
        if self._project:
            p_settings = self._project._settings
            if "timelineFrameRate" in p_settings:
                timeline.SetSetting("timelineFrameRate", p_settings["timelineFrameRate"])
            if "timelineResolutionWidth" in p_settings:
                timeline.SetSetting("timelineResolutionWidth", p_settings["timelineResolutionWidth"])
            if "timelineResolutionHeight" in p_settings:
                timeline.SetSetting("timelineResolutionHeight", p_settings["timelineResolutionHeight"])
            
            self._project.AddTimeline(timeline)
            
        return timeline


class MockTimelineItem:
    """Mock Timeline Item (clip on timeline)."""
    
    def __init__(self, name: str, start: int = 0, end: int = 100):
        self._name = name
        self._start = start
        self._end = end
        self._fusion_comps = []
        self._keyframes = {}  # {property: [{frame: 10, value: 1.0, interp: 0}]}
        self._keyframes = {}  # {property: [{frame: 10, value: 1.0, interp: 0}]}
        self._properties = {}
        self._grade = MockGrade()
    
    def GetCurrentGrade(self):
        return self._grade
    
    def GetName(self) -> str:
        return self._name
        
    def GetUniqueId(self) -> str:
        return f"id_{self._name}"
        
    def GetType(self) -> str:
        # Simple heuristic based on name or tracks can be added later
        # For now assume Video unless specified
        return "Video"
        
    def GetMediaType(self) -> str:
        return "Video"
    
    def GetStart(self) -> int:
        return self._start
    
    def GetEnd(self) -> int:
        return self._end
    
    def GetDuration(self) -> int:
        return self._end - self._start
    
    def GetFusionCompCount(self) -> int:
        return len(self._fusion_comps)
    
    def GetFusionCompByIndex(self, index: int):
        if 0 < index <= len(self._fusion_comps):
            return self._fusion_comps[index - 1]
        return None
    
    def AddFusionComp(self) -> bool:
        self._fusion_comps.append(MagicMock())
        return True
        
    def GetKeyframeCount(self, prop: str) -> int:
        return len(self._keyframes.get(prop, []))
        
    def GetKeyframeAtIndex(self, prop: str, index: int) -> Dict:
        if prop in self._keyframes and 0 <= index < len(self._keyframes[prop]):
            return self._keyframes[prop][index]
        return {}
        
    def GetPropertyAtKeyframeIndex(self, prop: str, index: int) -> float:
        if prop in self._keyframes and 0 <= index < len(self._keyframes[prop]):
            return self._keyframes[prop][index].get("value", 0.0)
        return 0.0
        
    def AddKeyframe(self, prop: str, frame: int, value: float, interp: int = 0) -> bool:
        if prop not in self._keyframes:
            self._keyframes[prop] = []
        
        # Check if exists and update
        for kf in self._keyframes[prop]:
            if kf["frame"] == frame:
                kf["value"] = value
                kf["interp"] = interp
                return True
                
        self._keyframes[prop].append({"frame": frame, "value": value, "interp": interp})
        # Sort by frame
        self._keyframes[prop].sort(key=lambda x: x["frame"])
        return True
        
    def DeleteKeyframe(self, prop: str, frame: int) -> bool:
        if prop in self._keyframes:
            initial_len = len(self._keyframes[prop])
            self._keyframes[prop] = [kf for kf in self._keyframes[prop] if kf["frame"] != frame]
            return len(self._keyframes[prop]) < initial_len
        return False
        
    def SetProperty(self, key: str, value: Any) -> bool:
        self._properties[key] = value
        return True
        
    def GetSourceStartFrame(self) -> int:
        return 0
        
    def GetSourceEndFrame(self) -> int:
        return 100
        
    def DeleteTakeByIndex(self, index: int) -> bool:
        return True
        
    def GetCurrentVersion(self) -> Dict[str, Any]:
        return {"versionName": "Version 1"}



class MockTimeline:
    """Mock Timeline."""
    
    def __init__(self, name: str):
        self._name = name
        self._settings = {
            "timelineFrameRate": "24",
            "timelineResolutionWidth": "1920",
            "timelineResolutionHeight": "1080"
        }
        self._video_tracks = [[]]  # List of tracks, each containing items
        self._audio_tracks = [[]]
        self._markers = {}
        self._start_frame = 0
        self._end_frame = 1000
    
    def GetName(self) -> str:
        return self._name
    
    def GetSetting(self, key: str) -> str:
        return self._settings.get(key, "")
    
    def SetSetting(self, key: str, value: str) -> bool:
        self._settings[key] = value
        return True
    
    def GetTrackCount(self, track_type: str) -> int:
        if track_type == "video":
            return len(self._video_tracks)
        elif track_type == "audio":
            return len(self._audio_tracks)
        return 0
    
    def GetTrackName(self, track_type: str, index: int) -> str:
        return f"{track_type.capitalize()} {index}"
    
    def GetItemListInTrack(self, track_type: str, index: int) -> List[MockTimelineItem]:
        tracks = self._video_tracks if track_type == "video" else self._audio_tracks
        if 0 < index <= len(tracks):
            return tracks[index - 1]
        return []
    
    def AddTrack(self, track_type: str, sub_type: str = None) -> bool:
        if track_type == "video":
            self._video_tracks.append([])
        elif track_type == "audio":
            self._audio_tracks.append([])
        return True
    
    def DeleteTrack(self, track_type: str, index: int) -> bool:
        tracks = self._video_tracks if track_type == "video" else self._audio_tracks
        if 0 < index <= len(tracks):
            tracks.pop(index - 1)
            return True
        return False
        
    def GetIsTrackEnabled(self, track_type: str, index: int) -> bool:
        return True
    
    def GetStartTimecode(self) -> str:
        return "01:00:00:00"
        
    def SetStartTimecode(self, timecode: str) -> bool:
        return True
    
    def GetMarkers(self) -> Dict:
        return self._markers
    
    def AddMarker(self, frame: int, color: str, name: str, note: str = "", duration: int = 1, customData: str = "") -> bool:
        self._markers[frame] = {"color": color, "name": name, "note": note, "duration": duration, "customData": customData}
        return True
    
    def GetStartFrame(self) -> int:
        return self._start_frame
    
    def GetEndFrame(self) -> int:
        return self._end_frame
    
    def InsertGeneratorIntoTimeline(self, name: str) -> bool:
        return True
    
    def InsertFusionTitleIntoTimeline(self, name: str) -> bool:
        return True

    def GetCurrentVideoItem(self):
        # Return the first item in the first video track if available
        if self._video_tracks and self._video_tracks[0]:
            return self._video_tracks[0][0]
        return None
        
    def SetCurrentSelectedItem(self, item) -> bool:
        return True
        
    def GetMarkInOut(self) -> Dict:
        return {"in": 0, "out": 100}

    def SetMarkInOut(self, in_point: int, out_point: int, type: str = "all") -> bool:
        return True

    def ClearMarkInOut(self, type: str = "all") -> bool:
        return True

    def GetTrackSubType(self, track_type: str, index: int) -> str:
        return "stereo"


class MockStill:
    """Mock Gallery Still."""
    def __init__(self, unique_id: str, label: str):
        self._id = unique_id
        self._label = label
    
    def GetUniqueId(self) -> str:
        return self._id
    
    def GetLabel(self) -> str:
        return self._label
    
    def SetLabel(self, label: str) -> bool:
        self._label = label
        return True
        
    def ApplyToClip(self) -> bool:
        return True
        
    def GetTimecode(self) -> str:
        return "01:00:00:00"
        
    def IsGrabbed(self) -> bool:
        return True


class MockGalleryAlbum:
    """Mock Gallery Album."""
    def __init__(self, name: str):
        self._name = name
        self._stills = []
    
    def GetName(self) -> str:
        return self._name
    
    def GetStills(self) -> List[MockStill]:
        return self._stills
    
    def DeleteStill(self, still: MockStill) -> bool:
        if still in self._stills:
            self._stills.remove(still)
            return True
        return False
        
    def DeleteStills(self, stills: List[MockStill]) -> bool:
        for still in stills:
            if still in self._stills:
                self._stills.remove(still)
        return True
        
    def AddStill(self, still: MockStill):
        self._stills.append(still)
        
    def GetLabel(self, still: MockStill) -> str:
        return still.GetLabel()
    
    def SetLabel(self, still: MockStill, label: str) -> bool:
        return still.SetLabel(label)


class MockGrade:
    """Mock Color Grade."""
    def __init__(self):
        self._nodes = {}
        self._current_node = 1
        self._node_count = 5
        
    def GetNodeCount(self) -> int:
        return self._node_count
    
    def GetCurrentNode(self) -> int:
        return self._current_node
    
    def SetCurrentNode(self, index: int) -> bool:
        if 1 <= index <= self._node_count:
            self._current_node = index
            return True
        return False
        
    def GetNodeName(self, index: int) -> str:
        return f"Node {index}"
    
    def GetNodeLabel(self, index: int) -> str:
        return f"Label {index}"
        
    def GetLUT(self, index: int) -> str:
        return f"LUT_{index}.cube"
        
    def ApplyLUT(self, index: int, path: str) -> bool:
        return True
    
    def ResetAllGrades(self) -> bool:
        return True


class MockGallery:
    """Mock Gallery."""
    def __init__(self):
        self._albums = [MockGalleryAlbum("DaVinci Resolve"), MockGalleryAlbum("PowerGrade")]
        self._current_album = self._albums[0]
    
    def GetAlbums(self) -> List[MockGalleryAlbum]:
        return self._albums
    
    def GetCurrentStillAlbum(self) -> MockGalleryAlbum:
        return self._current_album
    
    def CreateAlbum(self, name: str) -> MockGalleryAlbum:
        new_album = MockGalleryAlbum(name)
        self._albums.append(new_album)
        return new_album
        
    def DeleteAlbum(self, album: MockGalleryAlbum) -> bool:
        if album in self._albums:
            self._albums.remove(album)
            return True
        return False
        
    def GrabStill(self) -> bool:
        still = MockStill(f"id_{len(self._current_album._stills) + 1}", f"Still {len(self._current_album._stills) + 1}")
        self._current_album.AddStill(still)
        return True
        
    def GetGalleryStillAlbums(self) -> List[MockGalleryAlbum]:
        return self._albums
        
    def GetAlbumName(self, album: MockGalleryAlbum) -> str:
        return album.GetName()
    
    def GetLabel(self, still: MockStill) -> str:
        return still.GetLabel()


class MockProject:
    """Mock Project."""
    
    def __init__(self, name: str):
        self._name = name
        self._media_pool = MockMediaPool(self)
        self._gallery = MockGallery()
        self._timelines = [MockTimeline("Timeline 1")]
        self._current_timeline = self._timelines[0]
        self._settings = {}
        self._render_jobs = []
    
    def GetName(self) -> str:
        return self._name
    
    def AddTimeline(self, timeline: MockTimeline):
        self._timelines.append(timeline)
    
    def GetMediaPool(self) -> MockMediaPool:
        return self._media_pool
        
    def GetGallery(self) -> MockGallery:
        return self._gallery
    
    def GetTimelineCount(self) -> int:
        return len(self._timelines)
    
    def GetTimelineByIndex(self, index: int) -> MockTimeline:
        if 0 < index <= len(self._timelines):
            return self._timelines[index - 1]
        return None
    
    def GetCurrentTimeline(self) -> MockTimeline:
        return self._current_timeline
    
    def SetCurrentTimeline(self, timeline: MockTimeline) -> bool:
        self._current_timeline = timeline
        return True
    
    def GetSetting(self, key: str) -> str:
        return self._settings.get(key, "")
    
    def SetSetting(self, key: str, value: str) -> bool:
        self._settings[key] = value
        return True
    
    def GetRenderSettings(self):
        mock_render = MagicMock()
        mock_render.GetRenderPresetList.return_value = ["H.264 Master", "YouTube 1080p"]
        mock_render.GetSystemPresetList.return_value = ["ProRes 422", "DNxHR HQ"]
        return mock_render
    
    def AddRenderJob(self) -> str:
        job_id = f"job_{len(self._render_jobs) + 1}"
        self._render_jobs.append(job_id)
        return job_id
    
    def GetRenderJobList(self) -> List[str]:
        return self._render_jobs
    
    def DeleteAllRenderJobs(self) -> bool:
        self._render_jobs = []
        return True
        
    def DeleteTimelines(self, timelines: List[MockTimeline]) -> bool:
        for timeline in timelines:
            if timeline in self._timelines:
                self._timelines.remove(timeline)
        return True
    
    def LoadRenderPreset(self, name: str) -> bool:
        return True
        
    def ExportCurrentGradeAsLUT(self, format_index: int, size_index: int, path: str) -> bool:
        return True


class MockProjectManager:
    """Mock Project Manager."""
    
    def __init__(self):
        self._projects = {"Test Project": MockProject("Test Project")}
        self._current_project = self._projects["Test Project"]
    
    def GetCurrentProject(self) -> MockProject:
        return self._current_project
    
    def GetProjectListInCurrentFolder(self) -> List[str]:
        return list(self._projects.keys())
    
    def LoadProject(self, name: str) -> MockProject:
        if name in self._projects:
            self._current_project = self._projects[name]
            return self._current_project
        return None
    
    def CreateProject(self, name: str) -> MockProject:
        project = MockProject(name)
        self._projects[name] = project
        self._current_project = project
        return project


class MockResolve:
    """Mock DaVinci Resolve instance."""
    
    def __init__(self):
        self._project_manager = MockProjectManager()
        self._current_page = "edit"
        self._version = "19.0.0"
    
    def GetProjectManager(self) -> MockProjectManager:
        return self._project_manager
    
    def GetCurrentPage(self) -> str:
        return self._current_page
    
    def OpenPage(self, page: str) -> bool:
        valid_pages = ["media", "cut", "edit", "fusion", "color", "fairlight", "deliver"]
        if page in valid_pages:
            self._current_page = page
            return True
        return False
    
    def GetVersion(self) -> str:
        return self._version
    
    def GetProductName(self) -> str:
        return "DaVinci Resolve Studio"


# =====================
# Pytest Fixtures
# =====================

@pytest.fixture
def mock_resolve():
    """Create a mock DaVinci Resolve instance."""
    return MockResolve()


@pytest.fixture
def mock_project(mock_resolve):
    """Get the current mock project."""
    return mock_resolve.GetProjectManager().GetCurrentProject()


@pytest.fixture
def mock_timeline(mock_project):
    """Get the current mock timeline."""
    return mock_project.GetCurrentTimeline()


@pytest.fixture
def mock_media_pool(mock_project):
    """Get the mock media pool."""
    return mock_project.GetMediaPool()


@pytest.fixture
def sample_whisper_data():
    """Sample Whisper transcription output."""
    return {
        "text": "Hello world. This is a test video. After some silence we continue.",
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.5,
                "text": "Hello world.",
                "words": [
                    {"start": 0.0, "end": 0.5, "word": "Hello"},
                    {"start": 0.6, "end": 1.0, "word": "world."}
                ]
            },
            {
                "id": 1,
                "start": 3.0,
                "end": 6.0,
                "text": "This is a test video.",
                "words": [
                    {"start": 3.0, "end": 3.3, "word": "This"},
                    {"start": 3.4, "end": 3.6, "word": "is"},
                    {"start": 3.7, "end": 3.8, "word": "a"},
                    {"start": 3.9, "end": 4.3, "word": "test"},
                    {"start": 4.4, "end": 5.0, "word": "video."}
                ]
            },
            {
                "id": 2,
                "start": 10.0,
                "end": 14.0,
                "text": "After some silence we continue.",
                "words": [
                    {"start": 10.0, "end": 10.5, "word": "After"},
                    {"start": 10.6, "end": 11.0, "word": "some"},
                    {"start": 11.1, "end": 11.8, "word": "silence"},
                    {"start": 11.9, "end": 12.2, "word": "we"},
                    {"start": 12.3, "end": 13.0, "word": "continue."}
                ]
            }
        ],
        "language": "en"
    }


@pytest.fixture
def sample_clips(mock_media_pool):
    """Add sample clips to the media pool."""
    clips = [
        MockMediaPoolItem("Interview_A.mp4", {"FPS": "24", "Duration": "00:10:00:00"}),
        MockMediaPoolItem("Interview_B.mp4", {"FPS": "24", "Duration": "00:10:00:00"}),
        MockMediaPoolItem("B-Roll_01.mp4", {"FPS": "24", "Duration": "00:01:30:00"}),
        MockMediaPoolItem("B-Roll_02.mp4", {"FPS": "24", "Duration": "00:00:45:00"})
    ]
    for clip in clips:
        mock_media_pool._root_folder.AddClip(clip)
    return clips
