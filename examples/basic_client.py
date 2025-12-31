
import asyncio
import os
import sys

# Add the 'src' directory to sys.path so we can run the server script directly if needed,
# but here we want to use the MCP client to talk to the server process.

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to your server script
SERVER_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "resolve_mcp_server.py"))
VENV_PYTHON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "Scripts", "python.exe"))

async def run_client():
    # Define server parameters
    # We use the same environment as the server script requires
    env = os.environ.copy()
    
    # Create server parameters
    server_params = StdioServerParameters(
        command=VENV_PYTHON,
        args=[SERVER_SCRIPT],
        env=env
    )

    print(f"Starting server: {VENV_PYTHON} {SERVER_SCRIPT}")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            print("Connected to MCP Server")

            # List resources to see what's available
            resources = await session.list_resources()
            print("\nAvailable Resources:")
            for resource in resources.resources:
                print(f"- {resource.name} ({resource.uri})")

            # Try to read the version resource
            print("\nReading DaVinci Resolve Version:")
            try:
                result = await session.read_resource("resolve://version")
                print(f"Result: {result.contents[0].text}")
            except Exception as e:
                print(f"Error reading version: {e}")

            # Try to list projects
            print("\nListing Projects:")
            try:
                result = await session.read_resource("resolve://projects")
                # The result for this resource returns a list of strings JSON encoded? 
                # Or maybe it's just text content. Let's inspect.
                print(f"Result: {result.contents[0].text}")
            except Exception as e:
                print(f"Error listing projects: {e}")

            # List tools
            tools = await session.list_tools()
            print("\nAvailable Tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

if __name__ == "__main__":
    try:
        asyncio.run(run_client())
    except Exception as e:
        print(f"Client error: {e}")
