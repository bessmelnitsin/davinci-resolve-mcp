import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger("davinci-resolve-mcp.llm_client")

class LLMClient:
    """
    Universal Client for Chat Completion APIs (OpenAI-compatible).
    Defaults to OpenRouter.ai but supports local servers (Ollama, LM Studio).
    """
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        Initialize client.
        
        Args:
            api_key: standard API key (or read from env OPENROUTER_API_KEY)
            base_url: API endpoint (default: https://openrouter.ai/api/v1)
            model: Model name (default: google/gemini-2.0-flash-exp:free)
        """
        self._load_env()
        
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = base_url or os.environ.get("LOCAL_LLM_URL") or "https://openrouter.ai/api/v1"
        self.model = model or os.environ.get("OPENROUTER_MODEL") or "google/gemini-2.0-flash-exp:free"
        
        if not self.api_key and "openrouter" in self.base_url:
            logger.warning("LLMClient initialized without API Key! generation will likely fail.")

    def _load_env(self):
        """Simple .env loader"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k not in os.environ:
                            os.environ[k] = v.strip().strip('"').strip("'")

    def chat_complete(self, 
                      messages: List[Dict[str, str]], 
                      temperature: float = 0.7,
                      json_mode: bool = False) -> Optional[str]:
        """
        Send chat request to LLM.
        
        Args:
            messages: List of {"role": "user", "content": "..."}
            temperature: Creativity (0.0 - 2.0)
            json_mode: If True, asks for JSON response format
            
        Returns:
            String content of the response or None on failure
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/samuelgursky/davinci-resolve-mcp",
            "X-Title": "DaVinci Resolve MCP"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            logger.info(f"Sending request to {self.model} via {url}")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                return content
            else:
                logger.error(f"Unexpected API response format: {data}")
                return None
                
        except Exception as e:
            logger.error(f"LLM Request Failed: {e}")
            return None

    def test_connection(self) -> bool:
        """Verify API key works"""
        res = self.chat_complete([{"role": "user", "content": "Hello"}])
        return res is not None
