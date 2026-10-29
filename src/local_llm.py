"""
Local Ollama Large Language Model Interface.

Communicates exclusively over local HTTP with Ollama:
- Zero cloud transmission (strict privacy guarantee).
- Free and open-weight model execution.
- Graceful degradation when Ollama daemon is offline.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests


DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2:1b"
FALLBACK_MODELS = ["llama3.2:1b", "llama3.2:3b", "qwen2.5:1.5b", "qwen2.5:3b", "mistral:latest", "phi3:mini"]


def check_ollama_status(host: str = DEFAULT_OLLAMA_HOST, timeout: float = 2.0) -> Dict[str, Any]:
    """
    Test connectivity to the local Ollama daemon and list installed models.
    """
    url = f"{host.rstrip('/')}/api/tags"
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            models_list = [m.get("name") for m in data.get("models", []) if m.get("name")]
            return {
                "available": True,
                "host": host,
                "models": models_list,
                "message": f"Ollama is running locally. {len(models_list)} model(s) available.",
            }
        else:
            return {
                "available": False,
                "host": host,
                "models": [],
                "message": f"Ollama daemon returned HTTP {response.status_code}.",
            }
    except requests.exceptions.ConnectionError:
        return {
            "available": False,
            "host": host,
            "models": [],
            "message": "Ollama is not running locally. (Connection refused at http://127.0.0.1:11434)",
        }
    except Exception as e:
        return {
            "available": False,
            "host": host,
            "models": [],
            "message": f"Could not reach Ollama: {str(e)}",
        }


def generate_local_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    host: str = DEFAULT_OLLAMA_HOST,
    temperature: float = 0.2,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Query the local Ollama HTTP generation API without streaming.
    """
    url = f"{host.rstrip('/')}/api/generate"

    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("response", "").strip(),
                "model_used": model,
                "error": None,
            }
        elif response.status_code == 404:
            return {
                "success": False,
                "response": "",
                "model_used": model,
                "error": f"Model '{model}' not found in local Ollama library. Run: 'ollama pull {model}'",
            }
        else:
            return {
                "success": False,
                "response": "",
                "model_used": model,
                "error": f"Ollama HTTP error {response.status_code}: {response.text}",
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "response": "",
            "model_used": model,
            "error": f"Local model inference timed out after {timeout} seconds.",
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "response": "",
            "model_used": model,
            "error": "Connection to local Ollama daemon failed. Ensure 'ollama serve' is running.",
        }
    except Exception as e:
        return {
            "success": False,
            "response": "",
            "model_used": model,
            "error": f"Inference execution failed: {str(e)}",
        }
