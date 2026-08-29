from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_starts_without_exception():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not app.exception
    assert app.title[0].value == "Outlet Performance Intelligence"
    assert len(app.tabs) == 5
    assert len(app.get("plotly_chart")) == 7
    assert len(app.get("download_button")) == 2


def test_region_filter_updates_outlet_scope_without_exception():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    app.sidebar.multiselect[0].set_value(["West"]).run()
    assert not app.exception
    assert len(app.sidebar.multiselect[1].value) == 6
