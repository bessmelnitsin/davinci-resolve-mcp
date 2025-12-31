import os
import sys

def vlog(msg):
    print(msg)
    sys.stdout.flush()

vlog("Python version: " + sys.version)
vlog("CWD: " + os.getcwd())

RESOLVE_SCRIPT_API = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
RESOLVE_SCRIPT_LIB = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
RESOLVE_MODULES_PATH = os.path.join(RESOLVE_SCRIPT_API, "Modules")

vlog(f"Checking for DLL at: {RESOLVE_SCRIPT_LIB}")
vlog("DLL exists: " + str(os.path.exists(RESOLVE_SCRIPT_LIB)))

# DLL directory fix for Python 3.8+ on Windows
if hasattr(os, "add_dll_directory"):
    resolve_dir = os.path.dirname(RESOLVE_SCRIPT_LIB)
    vlog(f"Adding DLL directory: {resolve_dir}")
    os.add_dll_directory(resolve_dir)

vlog(f"Checking for Modules at: {RESOLVE_MODULES_PATH}")
vlog("Modules exist: " + str(os.path.exists(RESOLVE_MODULES_PATH)))

vlog("Setting environment variables...")
os.environ["RESOLVE_SCRIPT_API"] = RESOLVE_SCRIPT_API
os.environ["RESOLVE_SCRIPT_LIB"] = RESOLVE_SCRIPT_LIB

vlog("Inserting RESOLVE_MODULES_PATH into sys.path...")
sys.path.insert(0, RESOLVE_MODULES_PATH)

vlog("Attempting to import DaVinciResolveScript...")
try:
    import DaVinciResolveScript as dvr_script
    vlog("Import successful.")
    
    vlog("Attempting to get Resolve object via dvr_script.scriptapp('Resolve')...")
    resolve = dvr_script.scriptapp("Resolve")
    vlog("scriptapp('Resolve') call completed.")
    
    if resolve:
        vlog(f"Connected to DaVinci Resolve: {resolve.GetProductName()} {resolve.GetVersionString()}")
    else:
        vlog("Failed to get Resolve object (returned None).")
except Exception as e:
    vlog(f"Exception occurred: {e}")

vlog("Diagnostic finished.")
