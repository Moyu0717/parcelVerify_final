"""Test configuration: add project root to sys.path for imports."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture(autouse=True)
def _ai_review_in_foreground(monkeypatch):
    """Page tests check the finished review straight after the click, so run it in the page script."""
    import ui.workspace_ui
    monkeypatch.setattr(ui.workspace_ui, 'AI_IN_BACKGROUND', False)
