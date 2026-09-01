"""Test ChatWithTreeMCP dialog uses centralized settings."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_dialog_uses_config_map():
    import os
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ChatWithTreeMCP.py")
    with open(file_path) as f:
        source_text = f.read()
    assert "ChatWithTreeConfig.SETTINGS_MAP" in source_text
    assert "ChatWithTreeConfig.load_setting" in source_text
    assert "ChatWithTreeConfig.save_setting" in source_text
