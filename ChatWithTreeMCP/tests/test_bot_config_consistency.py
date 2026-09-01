"""Test ChatWithTreeBot uses centralized config interface."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_bot_uses_central_config():
    import ChatWithTreeBot as bot_mod
    import ChatWithTreeConfig as cfg_mod
    # Verify bot imports use load_setting / load_key_for_provider
    source_text = open(bot_mod.__file__).read()
    assert "load_setting" in source_text, "Bot should import load_setting"
    assert "load_key_for_provider" in source_text, "Bot should import load_key_for_provider"
