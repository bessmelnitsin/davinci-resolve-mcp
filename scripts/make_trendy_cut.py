import asyncio
import os
import sys
import json
import random

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Define paths
# Use main.py as it is the stable entry point
SERVER_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "main.py"))
VENV_PYTHON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "Scripts", "python.exe"))

async def make_trendy_cut():
    # Ensure environment variables for Resolve are set
    env = os.environ.copy()
    
    if sys.platform.startswith("win"):
        resolve_script_api = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
        resolve_script_lib = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
        
        env["RESOLVE_SCRIPT_API"] = resolve_script_api
        env["RESOLVE_SCRIPT_LIB"] = resolve_script_lib
        
        python_path = env.get("PYTHONPATH", "")
        modules_path = os.path.join(resolve_script_api, "Modules")
        if modules_path not in python_path:
            env["PYTHONPATH"] = f"{python_path};{modules_path}" if python_path else modules_path

    print("--- TRENDY CUT GENERATOR ---")
    print("Connecting to DaVinci Resolve MCP Server...")
    
    server_params = StdioServerParameters(
        command=VENV_PYTHON,
        args=[SERVER_SCRIPT],
        env=env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected!")

                # 1. Get available clips
                print("\nScanning Media Pool...")
                result = await session.read_resource("resolve://media-pool-clips")
                content_text = result.contents[0].text
                clips = json.loads(content_text)
                
                valid_clips = []
                if isinstance(clips, list):
                    for c in clips:
                        if "error" in c: continue
                        if "info" in c: continue
                        valid_clips.append(c)
                
                if not valid_clips:
                    print("No clips found in Media Pool! Please add some video files.")
                    return

                print(f"Found {len(valid_clips)} clips: {[c['name'] for c in valid_clips]}")

                # 2. Generate Edits
                edits = []
                timeline_name = "Trendy_Cut_Auto"
                num_cuts = 6
                
                print(f"\nGenerating {num_cuts} random cuts...")
                
                for i in range(num_cuts):
                    clip = random.choice(valid_clips)
                    # Random cut: start between 0-5s, duration 0.5-2.0s
                    start_time = random.uniform(0.0, 5.0) 
                    duration = random.uniform(0.5, 2.0)
                    
                    edits.append({
                        "clip_name": clip['name'],
                        "start_time": start_time,
                        "end_time": start_time + duration
                    })

                # 3. Call tool
                print(f"Calling create_trendy_timeline for '{timeline_name}'...")
                
                tool_result = await session.call_tool("create_trendy_timeline", 
                    arguments={
                        "edits": edits, 
                        "timeline_name": timeline_name
                    }
                )
                
                output_msg = tool_result.content[0].text
                print(f"\nSERVER RESPONSE: {output_msg}")
                print("Done! Check your 'Trendy_Cut_Auto' timeline in DaVinci Resolve.")
                
    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    asyncio.run(make_trendy_cut())
