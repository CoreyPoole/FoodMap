"""Smoke-test every Streamlit page against generated sample data."""
import glob
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
st_testing = pytest.importorskip("streamlit.testing.v1")

@pytest.fixture(scope="module", autouse=True)
def sample_db(tmp_path_factory):
    import db
    from generate_sample_data import generate
    from load_data import build_database
    d = tmp_path_factory.mktemp("app")
    generate(d / "data")
    build_database(d / "test.db", d / "data")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(db, "DB_PATH", d / "test.db")
        mp.setenv("FOODMAP_DB", str(db.DB_PATH))
        yield

@pytest.mark.parametrize("script", ["app.py"] + sorted(
    str(Path(p).relative_to(ROOT)) for p in glob.glob(str(ROOT / "pages" / "*.py"))))
def test_page_runs_without_exception(script):
    at = st_testing.AppTest.from_file(str(ROOT / script), default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
