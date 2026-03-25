import json
import os
import threading
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class LLMService:
    _rotation_lock = threading.Lock()
    _next_client_index = 0

    def __init__(self):
        try:
            from groq import Groq
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependency 'groq'. Install it before starting the backend."
            ) from exc

        self._groq_class = Groq
        self.config_path = self._resolve_config_path()
        self.model_names = self._load_model_names()
        self.clients = self._load_clients()

        if not self.clients:
            raise RuntimeError(
                "No Groq API keys found. Add them to backend/groq_keys.json or set GROQ_API_KEY."
            )

    def _resolve_config_path(self):
        env_path = os.getenv("GROQ_KEYS_FILE", "").strip()
        if env_path:
            return Path(env_path)
        return Path(__file__).resolve().parents[2] / "groq_keys.json"

    def _load_key_config(self):
        if not self.config_path.exists():
            return {}

        with self.config_path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)

    def _load_model_names(self):
        key_config = self._load_key_config()

        primary_model = (
            str(
                key_config.get("primary_model")
                or os.getenv("GROQ_MODEL")
                or "llama-3.3-70b-versatile"
            )
            .strip()
        )

        fallback_models = []

        config_fallbacks = key_config.get("fallback_models", [])
        if isinstance(config_fallbacks, list):
            fallback_models.extend(
                str(model_name).strip()
                for model_name in config_fallbacks
                if str(model_name).strip()
            )

        env_fallbacks = os.getenv("GROQ_FALLBACK_MODELS", "")
        fallback_models.extend(
            model.strip() for model in env_fallbacks.split(",") if model.strip()
        )

        fallback_models.extend(
            [
                "llama-3.1-8b-instant",
            ]
        )

        model_names = []
        for model_name in [primary_model, *fallback_models]:
            if model_name and model_name not in model_names:
                model_names.append(model_name)

        return model_names

    def _load_clients(self):
        key_config = self._load_key_config()
        api_keys = []

        config_keys = key_config.get("api_keys", [])
        if isinstance(config_keys, list):
            api_keys.extend(
                str(api_key).strip() for api_key in config_keys if str(api_key).strip()
            )

        env_keys = os.getenv("GROQ_API_KEYS", "")
        if env_keys:
            api_keys.extend(
                key.strip() for key in env_keys.split(",") if key.strip()
            )

        single_key = os.getenv("GROQ_API_KEY", "").strip()
        if single_key:
            api_keys.append(single_key)

        unique_keys = []
        for api_key in api_keys:
            normalized_key = api_key.strip()
            if not normalized_key:
                continue
            if "PASTE_GROQ_KEY_" in normalized_key:
                continue
            if normalized_key not in unique_keys:
                unique_keys.append(normalized_key)

        return [self._groq_class(api_key=api_key) for api_key in unique_keys]

    def _normalize_messages(self, messages):
        normalized_messages = []

        for message in messages:
            role = str(message.get("role", "user")).strip().lower()
            content = str(message.get("content", "")).strip()
            if not content:
                continue
            if role not in {"system", "user", "assistant"}:
                role = "user"
            normalized_messages.append({"role": role, "content": content})

        if not normalized_messages:
            raise ValueError("At least one non-empty message is required.")

        return normalized_messages

    def _client_order(self):
        with self._rotation_lock:
            start_index = self._next_client_index
            self._next_client_index = (self._next_client_index + 1) % len(self.clients)

        return [
            self.clients[(start_index + offset) % len(self.clients)]
            for offset in range(len(self.clients))
        ]

    def _should_try_next_client(self, error):
        status_code = getattr(error, "status_code", None)
        if status_code in {401, 403, 429}:
            return True

        message = str(error).lower()
        retry_markers = [
            "rate limit",
            "rate_limit",
            "quota",
            "tokens per day",
            "decommissioned",
            "no longer supported",
            "invalid api key",
            "authentication",
            "unauthorized",
            "forbidden",
            "connection error",
        ]
        return any(marker in message for marker in retry_markers)

    def generate(self, messages, temperature=0.2, max_tokens=2048):
        normalized_messages = self._normalize_messages(messages)
        last_error = None

        for client in self._client_order():
            for model_name in self.model_names:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=normalized_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    content = response.choices[0].message.content
                    return (content or "").strip()
                except Exception as exc:
                    last_error = exc
                    if self._should_try_next_client(exc):
                        continue
                    raise

        raise RuntimeError(f"LLM request failed across all Groq keys/models: {last_error}")
