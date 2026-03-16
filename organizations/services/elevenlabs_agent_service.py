from typing import Any, Dict, Optional

import requests
from django.conf import settings


class ElevenLabsAgentServiceError(Exception):
    def __init__(self, message: str, status_code: int = 502, details: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class ElevenLabsAgentService:
    BASE_URL = "https://api.elevenlabs.io"
    CREATE_AGENT_PATH = "/v1/convai/agents/create"

    @classmethod
    def _extract_agent_id(cls, payload: Dict[str, Any]) -> Optional[str]:
        if not isinstance(payload, dict):
            return None

        for key in ("agent_id", "agentId", "id"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("agent_id", "agentId", "id"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return None

    @classmethod
    def create_agent(
        cls,
        *,
        conversation_config: Dict[str, Any],
        name: Optional[str] = None,
        tags: Optional[list] = None,
        platform_settings: Optional[Dict[str, Any]] = None,
        workflow: Optional[Dict[str, Any]] = None,
        enable_versioning: bool = False,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        api_key = getattr(settings, "ELEVENLABS_API_KEY", "")
        if not api_key:
            raise ElevenLabsAgentServiceError(
                "ELEVENLABS_API_KEY is not configured",
                status_code=500,
            )

        payload: Dict[str, Any] = {
            "conversation_config": conversation_config,
        }
        if name:
            payload["name"] = name
        if tags is not None:
            payload["tags"] = tags
        if platform_settings is not None:
            payload["platform_settings"] = platform_settings
        if workflow is not None:
            payload["workflow"] = workflow

        try:
            response = requests.post(
                f"{cls.BASE_URL}{cls.CREATE_AGENT_PATH}",
                params={"enable_versioning": str(enable_versioning).lower()},
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise ElevenLabsAgentServiceError(
                "Failed to call ElevenLabs create agent API",
                status_code=502,
                details=str(exc),
            ) from exc

        if response.status_code >= 400:
            raise ElevenLabsAgentServiceError(
                "ElevenLabs create agent API returned an error",
                status_code=502,
                details=(response.text or "")[:1000],
            )

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise ElevenLabsAgentServiceError(
                "ElevenLabs create agent API returned invalid JSON",
                status_code=502,
                details=(response.text or "")[:1000],
            ) from exc

        agent_id = cls._extract_agent_id(response_payload)
        if not agent_id:
            raise ElevenLabsAgentServiceError(
                "ElevenLabs create agent response does not include agent_id",
                status_code=502,
                details=str(response_payload)[:1000],
            )

        return {
            "agent_id": agent_id,
            "raw": response_payload,
        }
