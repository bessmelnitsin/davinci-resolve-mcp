
import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Define paths
SERVER_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "resolve_mcp_server.py"))
VENV_PYTHON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "Scripts", "python.exe"))

async def test_timeline_features():
    env = os.environ.copy()
    server_params = StdioServerParameters(
        command=VENV_PYTHON,
        args=[SERVER_SCRIPT],
        env=env
    )

    print("--- ЗАПУСК ТЕСТА НОВЫХ ФУНКЦИЙ ---")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Server Connected.")

            # 1. List available clips first
            try:
                clips_result = await session.read_resource("resolve://media-pool-clips")
                # The result is a list of dicts, but serialized as a resource content? 
                # Actually resources return TextContent or BlobContent. 
                # Let's inspect tools instead to verify they exist.
                
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                
                if "append_clips_to_timeline" in tool_names and "create_timeline_from_clips" in tool_names:
                    print("[PASS] Новые инструменты обнаружены.")
                else:
                    print("[FAIL] Новые инструменты НЕ найдены.")
                    return
            except Exception as e:
                print(f"Error checking tools: {e}")
                return

            # 2. Try to creating a timeline from clips (requires knowing clip names)
            # For this test, we will assume there is at least ONE clip in the project.
            # We'll try to get clip names first.
             
            # !!! NOTE: This part depends on the 'list_media_pool_clips' resource returning JSON data in text format
            # or us parsing it. Since we can't easily parse the resource output in this simple script 
            # without knowing the exact format (it returns a list[dict] in python, but via MCP it's a string),
            # we will try to blindly add a clip named "Clip1" or similar if we can't get list.
            # actually, let's try to just run the tool with a dummy name and see if it returns a proper error,
            # which proves the tool is reachable.
            
            print("\n[TEST 1] Проверка create_timeline_from_clips (с несуществующим клипом)...")
            try:
                result = await session.call_tool("create_timeline_from_clips", 
                    arguments={"name": "TestTimeline_MCP", "clip_names": ["NON_EXISTENT_CLIP_12345"]})
                print(f"Result: {result.content[0].text}")
                if "Error: Clips not found" in result.content[0].text:
                     print("[PASS] Tool executed (handled missing clip correctly).")
                else:
                     print("[?] Unexpected response.")
            except Exception as e:
                print(f"[FAIL] Tool call failed: {e}")

            print("\n[TEST 2] Проверка append_clips_to_timeline (с несуществующим клипом)...")
            try:
                result = await session.call_tool("append_clips_to_timeline", 
                    arguments={"clip_names": ["NON_EXISTENT_CLIP_12345"]})
                print(f"Result: {result.content[0].text}")
                if "Error: Clips not found" in result.content[0].text:
                     print("[PASS] Tool executed (handled missing clip correctly).")
                else:
                     print("[?] Unexpected response.")
            except Exception as e:
                 print(f"[FAIL] Tool call failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_timeline_features())
