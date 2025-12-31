
import asyncio
import os
import sys
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Define paths
SERVER_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "resolve_mcp_server.py"))
VENV_PYTHON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "Scripts", "python.exe"))

async def demo_timeline():
    env = os.environ.copy()
    server_params = StdioServerParameters(
        command=VENV_PYTHON,
        args=[SERVER_SCRIPT],
        env=env
    )

    print("--- ЗАПУСК ДЕМОНСТРАЦИИ ТАЙМЛАЙНА ---")
    print("Подключение к серверу...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Успешное подключение к DaVinci Resolve!")

            # 1. List Clips
            print("\n[1] Сканирование Media Pool на наличие клипов...")
            try:
                # Read the resource
                result = await session.read_resource("resolve://media-pool-clips")
                
                # The content is a JSON string inside the text field
                content_text = result.contents[0].text
                
                # Parse JSON
                try:
                    clips = json.loads(content_text)
                    # Handle potential error response in JSON
                    if isinstance(clips, list) and len(clips) > 0 and "error" in clips[0]:
                        print(f"Ошибка от сервера: {clips[0]['error']}")
                        return
                    elif isinstance(clips, list) and len(clips) > 0 and "info" in clips[0]:
                        print("Media Pool пуст! Пожалуйста, добавьте хотя бы один клип в проект для демонстрации.")
                        return
                except json.JSONDecodeError:
                    # Fallback if it's not JSON (unlikely for this resource)
                    print(f"Не удалось разобрать ответ: {content_text}")
                    return

                clip_count = len(clips)
                print(f"Найдено клипов: {clip_count}")
                
                selected_clips = []
                if clip_count > 0:
                    selected_clips = [c['name'] for c in clips[:3]]
                else:
                    print("Список клипов пуст. Пробую использовать известные имена файлов (fallback)...")
                    # Fallback to clips found in debug_media_direct.py
                    selected_clips = ["C0002.MP4", "C0003.MP4", "C0006.MP4"]

                print(f"Выбраны для теста: {', '.join(selected_clips)}")
                
                # 2. Create Timeline
                timeline_name = "AI_Demo_Sequence"
                print(f"\n[2] Создание таймлайна '{timeline_name}' из выбранных клипов...")
                
                tool_result = await session.call_tool("create_timeline_from_clips", 
                    arguments={
                        "name": timeline_name, 
                        "clip_names": selected_clips
                    }
                )
                
                output_msg = tool_result.content[0].text
                print(f"Результат: {output_msg}")
                
                if "Error" in output_msg:
                    print("Произошла ошибка при создании.")
                else:
                    print("\n[УСПЕХ] Таймлайн создан! Проверьте вкладку Edit/Cut в DaVinci Resolve.")

                # 3. Add one more clip if available (just to show append)
                if clip_count > 3:
                    extra_clip = clips[3]['name']
                    print(f"\n[3] Добавление дополнительного клипа '{extra_clip}' в конец...")
                    append_result = await session.call_tool("append_clips_to_timeline",
                        arguments={
                            "clip_names": [extra_clip],
                            "timeline_name": timeline_name
                        }
                    )
                    print(f"Результат: {append_result.content[0].text}")

            except Exception as e:
                print(f"\n[!] Критическая ошибка в скрипте: {e}")

if __name__ == "__main__":
    asyncio.run(demo_timeline())
