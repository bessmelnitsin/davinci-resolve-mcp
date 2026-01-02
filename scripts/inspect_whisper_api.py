
import json
from gradio_client import Client

def inspect_api():
    try:
        print("Connecting to client...")
        c = Client("http://127.0.0.1:7860", verbose=False)
        print("Getting API info...")
        info = c.view_api(return_format="dict")
        
        with open("whisper_api_dump.json", "w") as f:
            json.dump(info, f, indent=2, default=str)
        print("Successfully dumped API to whisper_api_dump.json")
        
        # Print summary of analyze/transcribe endpoints
        endpoints = info.get("named_endpoints", {})
        for name, data in endpoints.items():
            if "transcribe" in name:
                print(f"Found endpoint: {name}")
                params = data.get("parameters", [])
                print(f"  Parameters: {len(params)}")
                for i, p in enumerate(params):
                    print(f"    [{i}] {p.get('label', '?')} ({p.get('parameter_name', '?')})")
                    if 'choices' in p:
                        print(f"       Choices: {p['choices']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_api()
