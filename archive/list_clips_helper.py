
import os
import sys

# Добавляем пути Resolve API
RESOLVE_SCRIPT_API = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
RESOLVE_SCRIPT_LIB = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
RESOLVE_MODULES_PATH = os.path.join(RESOLVE_SCRIPT_API, "Modules")

sys.path.append(RESOLVE_MODULES_PATH)
import DaVinciResolveScript as dvr_script

# Добавляем корень проекта для импортов
project_root = r"c:\GenModels\[Antigravity]\projects\test1\davinci-resolve-mcp"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_clips():
    resolve = dvr_script.scriptapp("Resolve")
    if not resolve:
        print("Error: Resolve not found")
        return
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()
    if not project:
        print("Error: No project open")
        return
        
    mp = project.GetMediaPool()
    
    from src.api.media_operations import get_all_media_pool_clips
    clips = get_all_media_pool_clips(mp)
    
    for clip in clips:
        print(f"CLIP:{clip.GetName()}")

if __name__ == "__main__":
    get_clips()
