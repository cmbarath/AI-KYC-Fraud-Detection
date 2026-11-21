import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.app.config import (
    Settings,
    _validate_database_url,
    _validate_model_artifacts,
    settings,
)


def test_vercel_data_dir_is_temporary_and_does_not_create_app_root_paths(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("BASE_DIR", str(tmp_path / "var" / "task"))
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.setattr("backend.app.config.tempfile.gettempdir", lambda: str(tmp_path))

    configured = Settings(_env_file=None)

    assert Path(configured.DATA_DIR) == tmp_path / "ai-kyc-data"
    assert not (Path(configured.BASE_DIR) / "data_samples").exists()
    assert not Path(configured.DATA_DIR).exists()


def test_local_data_dir_keeps_packaged_samples(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.delenv("BASE_DIR", raising=False)

    configured = Settings(_env_file=None)

    assert Path(configured.DATA_DIR) == Path(configured.BASE_DIR) / "data_samples"
    assert (
        Path(configured.DATA_DIR) / "sample_id_john_doe_pass.png"
    ).is_file()


def test_data_dir_environment_override_is_preserved(monkeypatch, tmp_path):
    override = tmp_path / "custom-data"
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("DATA_DIR", str(override))

    configured = Settings(_env_file=None)

    assert Path(configured.DATA_DIR) == override


def test_vercel_app_import_only_creates_temporary_runtime_directories(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    script = """
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import easyocr

root = Path(os.environ["AI_KYC_TEST_PROJECT_ROOT"]).resolve()
real_makedirs = os.makedirs
created_paths = []
def guarded_makedirs(path, *args, **kwargs):
    resolved = Path(path).resolve()
    assert resolved != root and root not in resolved.parents
    created_paths.append(resolved)
    return real_makedirs(path, *args, **kwargs)

with patch("os.makedirs", side_effect=guarded_makedirs), patch.object(
    easyocr, "Reader", return_value=SimpleNamespace(device="cpu")
):
    import backend.app.main as main
    import backend.app.config as config
    configured = config.Settings(_env_file=None)
    data_dir = Path(configured.DATA_DIR).resolve()
    assert main.app is not None
    assert data_dir == Path(tempfile.gettempdir()).resolve() / "ai-kyc-data"
    assert (
        Path(config.settings.MODEL_DIR).resolve()
        == root / "ml_engine" / "saved_models"
    )
    assert created_paths
    assert all(
        Path(tempfile.gettempdir()).resolve() == path
        or Path(tempfile.gettempdir()).resolve() in path.parents
        for path in created_paths
    )
"""
    environment = os.environ.copy()
    environment["VERCEL"] = "1"
    environment["DATABASE_URL"] = "postgresql+psycopg://test:test@localhost/test"
    environment["MODEL_DIR"] = str(project_root / "ml_engine" / "saved_models")
    environment["AI_KYC_TEST_PROJECT_ROOT"] = str(project_root)
    environment["TEMP"] = str(tmp_path)
    environment["TMP"] = str(tmp_path)
    environment.pop("DATA_DIR", None)
    environment.pop("BASE_DIR", None)

    subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


def test_vercel_rejects_file_backed_sqlite():
    with pytest.raises(RuntimeError, match="requires DATABASE_URL to use PostgreSQL"):
        _validate_database_url("sqlite:///backend/kyc_fraud.db", is_vercel=True)

    _validate_database_url("sqlite:///backend/kyc_fraud.db", is_vercel=False)


def test_missing_packaged_model_artifacts_fail_clearly(tmp_path):
    with pytest.raises(RuntimeError, match="Required packaged ML artifacts"):
        _validate_model_artifacts(str(tmp_path))


def test_packaged_models_remain_available():
    model_dir = Path(settings.MODEL_DIR)
    assert model_dir == Path(settings.BASE_DIR) / "ml_engine" / "saved_models"
    from backend.app.services.fraud_service import fraud_service

    assert {
        "random_forest",
        "xgboost",
        "logistic_regression",
    } <= set(fraud_service.models)


def test_vercel_easyocr_cache_uses_tempdir_and_cpu(monkeypatch, tmp_path):
    from backend.app.services import ocr_service as ocr_module

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(ocr_module.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(ocr_module.OCRService, "_instance", None)
    monkeypatch.setattr(ocr_module.OCRService, "_reader", None)
    reader = SimpleNamespace(device="cpu")

    with patch.object(ocr_module.easyocr, "Reader", return_value=reader) as create_reader:
        service = ocr_module.OCRService()

    assert service._reader.device == "cpu"
    assert create_reader.call_args.args == (["en"],)
    assert create_reader.call_args.kwargs == {
        "gpu": False,
        "model_storage_directory": os.path.join(str(tmp_path), ".EasyOCR"),
    }
