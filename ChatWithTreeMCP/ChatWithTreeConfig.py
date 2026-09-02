# Shared configuration for ChatWithTreeMCP
# Both ChatWithTreeBot.py (backend) and ChatWithTreeMCP.py (GUI) import this.
# Standard plugin architecture: single manager (register_manager) only.


from gramps.gen.config import config

_CONFIG = config.register_manager("ChatWithTreeMCP")
# Temporary in-memory cache for model lists fetched at settings-open time.
# Not persisted to .ini; cleared/rebuilt per settings session.
_MODEL_OPTIONS_CACHE: dict[str, list[str]] = {}
# Flag set when any API-key setting changes; triggers model list reload.
_MODEL_OPTIONS_CACHE_RELOAD_NEEDED: bool = True


class ChatConfig:
    """Config holder to prevent bare module-level globals for cache/reload state."""

    def __init__(self):
        self._model_options_cache: dict[str, list[str]] = {}
        self._model_options_reload_needed: bool = True

    def get_all_models(self) -> dict[str, list[str]]:
        """Public interface for iteration over all cached provider/model lists."""
        return self._model_options_cache.copy()

    def fetch_model_lists(self):
        import logging

        if not self._model_options_reload_needed:
            return
        self._model_options_reload_needed = False
        log = logging.getLogger("ChatWithTreeMCP")
        for provider, cfg_key in {
            "openrouter": "openrouter_api_key",
            "openai": "openai_api_key",
            "deepseek": "deepseek_api_key",
            "moonshotai": "moonshotai_api_key",
            "ollama": None,
            "opencode": "opencode_api_key",
        }.items():
            url_val = _CONFIG.get("settings.model_url") or "http://localhost:11434"
            key_val = _CONFIG.get(f"settings.{cfg_key}") if cfg_key else ""
            if cfg_key and not key_val:
                self._model_options_cache[provider] = []
                log.warning(f"[models] provider={provider} skipped (no api_key)")
                continue
            try:
                from llm_client import PROVIDER_REGISTRY, LLMClient

                client = LLMClient()
                reg = PROVIDER_REGISTRY.get(provider)
                base_url = (
                    reg.get("base_url")
                    if reg
                    else (url_val or "http://localhost:11434")
                ) or "http://localhost:11434"
                models_path = (
                    reg.get("models_path", "/v1/models") if reg else "/v1/models"
                )
                url_val = base_url.rstrip("/") + models_path
                endpoint = url_val
                log.warning(
                    f"[models] provider={provider} endpoint={endpoint} url={url_val} key_present={'yes' if key_val else 'no'}"
                )
                fetched = client.list_models(base_url, key_val)
                self._model_options_cache[provider] = fetched
                log.warning(
                    f"[models] provider={provider} endpoint={endpoint} fetched={len(fetched)} url={base_url}"
                )
            except (TypeError, ValueError, KeyError) as exc:
                self._model_options_cache[provider] = []
                log.warning(f"[models] provider={provider} fetch failed: {exc}")


# Module-level alias (backward compatible with existing references)
_chat_config = ChatConfig()
_MODEL_OPTIONS_CACHE = _chat_config._model_options_cache
_MODEL_OPTIONS_CACHE_RELOAD_NEEDED = _chat_config._model_options_reload_needed
_CONFIG.register("settings.model_name", "ollama/deepseek-r1:1.5b")
_CONFIG.register("settings.model_url", "http://localhost:11434")
_CONFIG.register("settings.loop_limit", 6)
_CONFIG.register("settings.openrouter_api_key", "")
_CONFIG.register("settings.opencode_api_key", "")
_CONFIG.register("settings.openai_api_key", "")
_CONFIG.register("settings.deepseek_api_key", "")
_CONFIG.register("settings.moonshotai_api_key", "")
_CONFIG.register("settings.gemini_api_key", "")
_CONFIG.register("settings.anthropic_api_key", "")
_CONFIG.register("settings.groq_api_key", "")
_CONFIG.register("settings.mistral_api_key", "")

_CONFIG.load()


SETTINGS_MAP = {
    "model_name": ("Model (with prefix, e.g. openrouter/...)", "ollama/gemma4"),
    "model_url": ("Ollama URL (local endpoint override)", "http://localhost:11434"),
    "loop_limit": ("Loop limit", 6),
    "openrouter_api_key": ("OpenRouter API Key", ""),
    "opencode_api_key": ("OpenCode API Key", ""),
    "openai_api_key": ("OpenAI API Key", ""),
    "deepseek_api_key": ("DeepSeek API Key", ""),
    "moonshotai_api_key": ("MoonshotAI API Key", ""),
    "gemini_api_key": ("Gemini API Key", ""),
    "anthropic_api_key": ("Anthropic API Key", ""),
    "groq_api_key": ("Groq API Key", ""),
    "mistral_api_key": ("Mistral API Key", ""),
}


def _cfg(key, fallback=""):
    try:
        v = _CONFIG.get("settings." + key)
        if v is not None:
            return v
    except (KeyError, ValueError):
        # Config registry isolation: return fallback silently
        pass
    return fallback


PROVIDER_KEY_MAP = {
    "ollama": None,
    "openrouter": "openrouter_api_key",
    "opencode": "opencode_api_key",
    "openai": "openai_api_key",
    "deepseek": "deepseek_api_key",
    "moonshotai": "moonshotai_api_key",
    "gemini": "gemini_api_key",
    "anthropic": "anthropic_api_key",
    "groq": "groq_api_key",
    "mistral": "mistral_api_key",
}


def verify_settings_registered():
    for key in SETTINGS_MAP:
        prefixed = "settings." + key
        v = _CONFIG.get(prefixed)
        assert v is not None or SETTINGS_MAP[key][1] is not None, (
            f"Setting {key} not registered in manager"
        )


def load_key_for_provider(provider):
    cfg_key = PROVIDER_KEY_MAP.get(provider)
    if cfg_key is None:
        return None
    return _cfg(cfg_key, "")


def load_setting(key):
    _label, default = SETTINGS_MAP[key]
    _CONFIG.load()
    val = _cfg(key, default)
    # Gramps suppresses LOG.info; LOG.warn is visible in Gramps logs
    # Intentionally not logging all settings to keep logs clean
    return val


def save_setting(key, value):
    _label, default = SETTINGS_MAP[key]
    # loop_limit stored as int in manager but saved as string for manager
    if key == "loop_limit":
        value = (
            int(value)
            if str(value).isdigit()
            else (default if isinstance(default, int) else 6)
        )
    else:
        value = str(value) if value is not None else default
    # Detect API-key changes to trigger model list reload
    prev = load_setting(key)
    if key.endswith("_api_key"):
        prev_str = str(prev or "")
        new_str = str(value or "")
        if prev_str != new_str:
            # Update instance flag directly (not module alias)
            _chat_config._model_options_reload_needed = True
    _CONFIG.set("settings." + key, value)
    _CONFIG.save()
    _CONFIG.load()
