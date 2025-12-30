"""Smoke tests for the Streamlit UI page."""

from streamlit.testing.v1 import AppTest


def test_streamlit_page_renders() -> None:
    """Ensure the main Streamlit page renders without errors."""
    at = AppTest.from_file("src/buckutils/app.py").run()

    assert not at.exception
    assert any("BuckUtils PDF Helper" in title.value for title in at.title)
