"""Test that load_setting reloads manager from .ini."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_load_setting_reload():
    import ChatWithTreeConfig as cfg_mod

    cfg_mod.save_setting("model_name", "test_reload")
    # After save, load_setting must read the new value (calls _CONFIG.load())
    val = cfg_mod.load_setting("model_name")
    assert val == "test_reload", f"Expected 'test_reload', got {val!r}"
