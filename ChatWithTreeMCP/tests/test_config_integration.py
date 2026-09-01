"""Integration: save via config -> read via config -> value matches."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_integrated_config_roundtrip():
    import ChatWithTreeConfig as cfg_mod
    # Save a test value
    cfg_mod.save_setting("model_name", "integration_test_model")
    # Read back via load_setting (should reload .ini)
    val = cfg_mod.load_setting("model_name")
    assert val == "integration_test_model", f"Integration failed: {val!r}"
    # Restore default
    cfg_mod.save_setting("model_name", cfg_mod.SETTINGS_MAP["model_name"][1])
