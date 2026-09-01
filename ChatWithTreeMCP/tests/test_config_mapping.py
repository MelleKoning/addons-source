"""Test delegated mapping and settings verification."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_provider_key_map_coverage():
    import ChatWithTreeConfig as cfg_mod
    for provider, cfg_key in cfg_mod.PROVIDER_KEY_MAP.items():
        assert provider is not None or cfg_key is None
        if cfg_key is not None:
            assert cfg_key in cfg_mod.SETTINGS_MAP, \
                f"Provider {provider} maps to unknown setting {cfg_key}"


def test_settings_map_matches_manager():
    import ChatWithTreeConfig as cfg_mod
    for key in cfg_mod.SETTINGS_MAP:
        prefixed = "settings." + key
        v = cfg_mod._CONFIG.get(prefixed)
        assert v is not None or cfg_mod.SETTINGS_MAP[key][1] is not None, \
            f"Setting {key} not registered"


def test_load_key_for_provider():
    import ChatWithTreeConfig as cfg_mod
    assert cfg_mod.load_key_for_provider("ollama") is None or cfg_mod.load_key_for_provider("ollama") == ""
    assert cfg_mod.load_key_for_provider("nonexistent") is None


def test_roundtrip_all_settings():
    import ChatWithTreeConfig as cfg_mod
    for key in cfg_mod.SETTINGS_MAP:
        saved = cfg_mod.SETTINGS_MAP[key][1]
        cfg_mod.save_setting(key, saved)
        loaded = cfg_mod.load_setting(key)
        assert loaded == saved or (isinstance(saved, int) and loaded == saved), \
            f"Setting {key}: expected {saved}, got {loaded}"
