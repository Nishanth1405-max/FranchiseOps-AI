from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_starts_without_exception():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == "Outlet Performance Intelligence"
    assert len(app.tabs) == 9
    assert len(app.get("plotly_chart")) == 14
    assert len(app.get("download_button")) == 6
    assert len(app.selectbox) == 5


def test_milestone2_agent_outputs_are_visible_without_exception():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    milestone2_selectors = [
        selectbox for selectbox in app.selectbox
        if selectbox.label == "Select Milestone 2 outlet"
    ]
    assert len(milestone2_selectors) == 3
    assert any(option.startswith("OUT0706") for option in milestone2_selectors[0].options)
    assert "OUT0706" in milestone2_selectors[1].options
    assert any(option.startswith("OUT0706") for option in milestone2_selectors[2].options)
    assert any("Staff Agent" in markdown.value for markdown in app.markdown)
    assert any("Marketing Agent" in markdown.value for markdown in app.markdown)
    assert any("Inventory Agent and Forecasting" in markdown.value for markdown in app.markdown)


def test_region_filter_updates_outlet_scope_without_exception():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    app.sidebar.multiselect[0].set_value(["West"]).run()
    assert not app.exception
    assert len(app.sidebar.multiselect[1].value) == 6
