"""Test ChatWithTreeBot uses centralized config interface."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_bot_uses_central_config():
    import ChatWithTreeBot as bot_mod

    # Haal het pad naar het bestand op
    bot_file_path = bot_mod.__file__

    # Open het bestand netjes met een context manager volgens de Ruff-richtlijn
    with open(bot_file_path, "r", encoding="utf-8") as f:
        source_text = f.read()

    # De functionele asserts blijven exact hetzelfde
    assert "load_setting" in source_text, "Bot should import load_setting"
    assert "load_key_for_provider" in source_text, (
        "Bot should import load_key_for_provider"
    )
