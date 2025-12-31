
import os
import sys

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import DaVinci API manually
RESOLVE_SCRIPT_API = os.environ.get("RESOLVE_SCRIPT_API", r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
RESOLVE_MODULES_PATH = os.path.join(RESOLVE_SCRIPT_API, "Modules")
sys.path.append(RESOLVE_MODULES_PATH)

try:
    import DaVinciResolveScript as dvr_script
    resolve = dvr_script.scriptapp("Resolve")
    if not resolve:
        print("Could not connect to Resolve")
        sys.exit(1)
except ImportError:
    print("Could not import DaVinciResolveScript")
    sys.exit(1)

print(f"Connected: {resolve.GetProductName()}")

# Import our function
from src.api.media_operations import get_all_media_pool_clips

project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
media_pool = project.GetMediaPool()

print("--- DEBUGGING MEDIA POOL ---")
root = media_pool.GetRootFolder()
print(f"Root Folder: {root.GetName()}")

# List immediate children
clips = root.GetClipList()
print(f"Root Clips: {len(clips)}")
for c in clips:
    print(f" - {c.GetName()}")

folders = root.GetSubFolderList()
print(f"Root SubFolders: {len(folders)}")
for f in folders:
    print(f" - Folder: {f.GetName()}")
    f_clips = f.GetClipList()
    print(f"   - Clips: {len(f_clips)}")

print("\n--- TEST RECURSIVE FUNCTION ---")
all_clips = get_all_media_pool_clips(media_pool)
print(f"Total Clips Found: {len(all_clips)}")
for c in all_clips:
    print(f" * {c.GetName()}")
