"""Test configuration and fixtures."""

import sys
from unittest.mock import MagicMock

# Mock tkinter for headless testing environments
if "tkinter" not in sys.modules:
    sys.modules["tkinter"] = MagicMock()
    sys.modules["tkinter.ttk"] = MagicMock()
    sys.modules["tkinter.filedialog"] = MagicMock()
    sys.modules["tkinter.messagebox"] = MagicMock()
