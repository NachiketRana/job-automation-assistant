import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import urllib.request
import urllib.error

class InvisibleDotsClient:
    """
    Client for interacting with the local invisible_dots control plane API (default http://127.0.0.1:8787).
    Allows job-automation-assistant to dispatch undetectable stealth browser automations,
    query VM status, and stream real-time thoughts and tool events.
    """
    DEFAULT_BASE_URL = "http://127.0.0.1:8787"

    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token or self._load_token()

    def _load_token(self) -> str:
        """Reads the local API token from ~/.invisible-dots/config/api.token."""
        token_path = Path.home() / ".invisible-dots" / "config" / "api.token"
        if token_path.exists():
            return token_path.read_text(encoding="utf-8").strip()
        return os.environ.get("INVISIBLE_DOTS_TOKEN", "")

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def is_server_online(self) -> bool:
        """Checks if the local invisible-dots server is reachable and healthy."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/health",
                headers=self._get_headers(),
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    return data.get("status") == "ok"
        except Exception:
            return False
        return False

    def get_server_health(self) -> Dict[str, Any]:
        """Returns the full health and configuration status of invisible-dots."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/health",
                headers=self._get_headers(),
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def list_dots(self) -> List[Dict[str, Any]]:
        """Lists all existing Dots (agent VMs)."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/dots",
                headers=self._get_headers(),
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                return data.get("dots", [])
        except Exception as e:
            return []

    def get_or_create_job_dot(self, dot_name: str = "job-copilot", model_id: str = "google/gemini-2.0-flash-001") -> Dict[str, Any]:
        """
        Finds or provisions a dedicated Job Hunter Dot with invisible-playwright capabilities.
        """
        existing = self.list_dots()
        for d in existing:
            if d.get("name") == dot_name or d.get("id") == dot_name:
                return d

        # Provision a new Dot
        payload = {
            "config": {
                "name": dot_name,
                "model": {
                    "provider": "openrouter",
                    "id": model_id
                },
                "limits": {
                    "max_steps_per_task": 60,
                    "max_cost_per_task_usd": 1.0
                },
                "computer": {
                    "cpu": 2,
                    "disk": "40gb",
                    "memory": "4gb",
                    "idle_timeout": "15m"
                }
            }
        }
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/dots",
                data=json.dumps(payload).encode("utf-8"),
                headers=self._get_headers(),
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            return {"error": f"HTTP {e.code}", "details": err_body}
        except Exception as e:
            return {"error": str(e)}

    def send_task(self, dot_name: str, task_prompt: str, priority: int = 0) -> Dict[str, Any]:
        """
        Submits an asynchronous task to a Dot VM.
        e.g. 'Navigate to Wellfound, find Full-Stack jobs in India, and extract the top 5 listings.'
        """
        payload = {
            "prompt": task_prompt,
            "priority": priority
        }
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/dots/{dot_name}/tasks",
                data=json.dumps(payload).encode("utf-8"),
                headers=self._get_headers(),
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP {e.code}", "details": e.read().decode()}
        except Exception as e:
            return {"error": str(e)}

    def get_task_status(self, dot_name: str, task_id: str) -> Dict[str, Any]:
        """Polls the status, steps, and outputs of a task."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/dots/{dot_name}/tasks/{task_id}",
                headers=self._get_headers(),
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    client = InvisibleDotsClient()
    print("Testing connection to invisible_dots...")
    health = client.get_server_health()
    print("Server Health:", json.dumps(health, indent=2))
    dots = client.list_dots()
    print(f"Discovered {len(dots)} Dot(s):")
    for d in dots:
        print(f" - {d.get('name')} ({d.get('id')}) | Status: {d.get('status')}")
