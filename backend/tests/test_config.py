import pytest

from app.utils.config import PROJECT_ROOT, Settings


def test_production_refuses_default_secret_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings(APP_ENV="production", SECRET_KEY="change-me-in-production").check_production_safety()


def test_production_accepts_a_real_secret():
    Settings(APP_ENV="production", SECRET_KEY="x" * 40, DEBUG=False).check_production_safety()


def test_relative_paths_resolve_from_project_root():
    assert Settings(DATASET_PATH="dataset/a.json").dataset_path == PROJECT_ROOT / "dataset" / "a.json"
