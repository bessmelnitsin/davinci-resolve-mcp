
import asyncio
import os
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Define the server script path
SERVER_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "resolve_mcp_server.py"))
VENV_PYTHON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "Scripts", "python.exe"))

async def prove_it():
    # Define server parameters
    env = os.environ.copy()
    server_params = StdioServerParameters(
        command=VENV_PYTHON,
        args=[SERVER_SCRIPT],
        env=env
    )

    print(f"Запускаю сервер для демонстрации...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("--- ПОДКЛЮЧЕНО К DAVINCI RESOLVE ---")

            # 1. Get Version
            try:
                result = await session.read_resource("resolve://version")
                print(f"\n[1] Версия DaVinci: {result.contents[0].text}")
            except Exception as e:
                print(f"[!] Ошибка получения версии: {e}")

            # 2. Get Current Project
            try:
                result = await session.read_resource("resolve://current-project")
                print(f"[2] Текущий проект: {result.contents[0].text}")
            except Exception as e:
                print(f"[!] Ошибка получения проекта: {e}")

            # 3. Get Current Page
            try:
                result = await session.read_resource("resolve://current-page")
                page_start = result.contents[0].text
                print(f"[3] Текущая страница: {page_start}")
            except:
                page_start = "edit"

            # 4. Switch Pages (Visual Demo)
            print("\n[4] ДЕМОНСТРАЦИЯ УПРАВЛЕНИЯ (Смотрите на экран DaVinci!)")
            
            target_page = "color" if page_start.lower() != "color" else "edit"
            print(f"--> Переключаем на страницу '{target_page}'...")
            await session.call_tool("switch_page", arguments={"page": target_page})
            
            print("--> Ждем 3 секунды...")
            await asyncio.sleep(3)
            
            print(f"--> Возвращаем на страницу '{page_start}'...")
            await session.call_tool("switch_page", arguments={"page": page_start})

            print("\n--- ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА ---")

if __name__ == "__main__":
    try:
        asyncio.run(prove_it())
    except Exception as e:
        print(f"Critical Error: {e}")
