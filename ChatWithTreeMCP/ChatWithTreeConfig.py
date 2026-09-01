# Shared configuration for ChatWithTreeMCP
# Both ChatWithTreeBot.py (backend) and ChatWithTreeMCP.py (GUI) import this.
# Standard plugin architecture: single manager (register_manager) only.

from gramps.gen.config import config

_CONFIG = config.register_manager("ChatWithTreeMCP")
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
    "model_name":     ("Model (with prefix, e.g. openrouter/...)", "ollama/gemma4"),
    "model_url":      ("Ollama URL (local endpoint override)", "http://localhost:11434"),
    "loop_limit":     ("Loop limit", 6),
    "openrouter_api_key":     ("OpenRouter API Key", ""),
    "opencode_api_key":       ("OpenCode API Key", ""),
    "openai_api_key":         ("OpenAI API Key", ""),
    "deepseek_api_key":       ("DeepSeek API Key", ""),
    "moonshotai_api_key":     ("MoonshotAI API Key", ""),
    "gemini_api_key":         ("Gemini API Key", ""),
    "anthropic_api_key":      ("Anthropic API Key", ""),
    "groq_api_key":           ("Groq API Key", ""),
    "mistral_api_key":        ("Mistral API Key", ""),
}


def _cfg(key, fallback=""):
    try:
        v = _CONFIG.get("settings." + key)
        if v is not None:
            return v
    except Exception:
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
        assert v is not None or SETTINGS_MAP[key][1] is not None, \
            f"Setting {key} not registered in manager"


def load_key_for_provider(provider):
    cfg_key = PROVIDER_KEY_MAP.get(provider)
    if cfg_key is None:
        return None
    return _cfg(cfg_key, "")


def load_setting(key):
    label, default = SETTINGS_MAP[key]
    _CONFIG.load()
    val = _cfg(key, default)
    # Gramps suppresses LOG.info; LOG.warn is visible in Gramps logs
    import logging
    log = logging.getLogger("ChatWithTreeConfig")
    log.warning(f"[ChatWithTreeConfig] load_setting({key}) = {val!r}")
    return val


def save_setting(key, value):
    label, default = SETTINGS_MAP[key]
    # loop_limit stored as int in manager but saved as string for manager
    if key == "loop_limit":
        value = int(value) if str(value).isdigit() else \
            (default if isinstance(default, int) else 6)
    else:
        value = str(value) if value is not None else default
    _CONFIG.set("settings." + key, value)
    _CONFIG.save()
    _CONFIG.load()
