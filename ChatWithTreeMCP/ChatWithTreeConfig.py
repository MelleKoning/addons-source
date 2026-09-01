# Shared configuration for ChatWithTreeMCP
# Both ChatWithTreeBot.py (backend) and ChatWithTreeMCP.py (GUI) import this.
import os

try:
    from gramps.gen.config import config
    _CONFIG = config.register_manager("ChatWithTreeMCP")
    _CONFIG.register("model_name", "ollama/deepseek-r1:1.5b")
    _CONFIG.register("model_url", "http://localhost:11434")
    _CONFIG.register("loop_limit", 6)
    _CONFIG.register("openrouter_api_key", "")
    _CONFIG.register("opencode_api_key", "")
    _CONFIG.register("openai_api_key", "")
    _CONFIG.register("deepseek_api_key", "")
    _CONFIG.register("moonshotai_api_key", "")
    _CONFIG.register("gemini_api_key", "")
    _CONFIG.register("anthropic_api_key", "")
    _CONFIG.register("groq_api_key", "")
    _CONFIG.register("mistral_api_key", "")
    _CONFIG.load()
except Exception:
    _CONFIG = None


def _cfg(key, fallback=""):
    try:
        import configparser
        ini_path = os.path.join(os.path.dirname(__file__), "ChatWithTreeMCP.ini")
        if os.path.exists(ini_path):
            cp = configparser.ConfigParser()
            cp.read(ini_path)
            if cp.has_option("ChatWithTreeMCP", key):
                return cp.get("ChatWithTreeMCP", key)
    except Exception:
        pass
    try:
        if _CONFIG is not None:
            v = _CONFIG.get(key)
            if v is not None:
                return v
    except Exception:
        pass
    try:
        from gramps.gen.config import config
        return config.get(f"ChatWithTreeMCP.{key}")
    except Exception:
        pass
    return fallback


GRAMPS_AI_MODEL_NAME = (
    _cfg("model_name") or os.environ.get("GRAMPS_AI_MODEL_NAME")
)
GRAMPS_AI_MODEL_URL = (
    _cfg("model_url") or os.environ.get("GRAMPS_AI_MODEL_URL", "http://localhost:11434")
)
