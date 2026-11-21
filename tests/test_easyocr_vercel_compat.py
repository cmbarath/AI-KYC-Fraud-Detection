import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from backend.app.easyocr_compat import pillow_imread


@pytest.mark.parametrize(
    ("mode", "extension", "color", "expected", "tolerance"),
    [
        ("RGB", ".jpg", (214, 45, 17), (214, 45, 17), 3),
        ("RGB", ".png", (15, 67, 201), (15, 67, 201), 0),
        ("L", ".png", 71, (71, 71, 71), 0),
        ("RGBA", ".png", (11, 37, 89, 0), (11, 37, 89), 0),
    ],
)
def test_pillow_image_reader_returns_rgb_with_expected_shape(
    tmp_path, mode, extension, color, expected, tolerance
):
    path = tmp_path / f"image{extension}"
    Image.new(mode, (9, 7), color).save(path)

    image = pillow_imread(str(path))

    assert image.shape == (7, 9, 3)
    assert image.dtype == np.uint8
    np.testing.assert_allclose(image[0, 0], expected, atol=tolerance)


def test_pillow_image_reader_accepts_encoded_bytes(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (4, 3), (23, 45, 67)).save(path)

    image = pillow_imread(path.read_bytes())

    assert image.shape == (3, 4, 3)
    np.testing.assert_array_equal(image[0, 0], (23, 45, 67))


def test_non_vercel_import_uses_real_scikit_image():
    project_root = Path(__file__).resolve().parents[1]
    script = """
import os
os.environ.pop("VERCEL", None)
import skimage
from backend.app.easyocr_compat import import_easyocr, pillow_imread

easyocr = import_easyocr()
assert easyocr.imgproc.io.__name__ == "skimage.io"
assert easyocr.imgproc.io is skimage.io
assert easyocr.imgproc.io.imread is not pillow_imread
assert skimage.__file__
"""
    environment = os.environ.copy()
    environment.pop("VERCEL", None)

    subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


def test_actual_ocr_processes_packaged_synthetic_sample():
    from backend.app.config import settings
    from backend.app.services.ocr_service import ocr_service

    sample = Path(settings.BASE_DIR) / "data_samples" / "sample_id_john_doe_pass.png"
    result = ocr_service.extract_text_and_entities(str(sample))

    assert isinstance(result["raw_text"], str)
    assert result["raw_text"]
    assert result["quality_report"]["tamper_suspected"] in (True, False)


def test_easyocr_runs_on_cpu_and_random_forest_shap_still_work():
    from backend.app.schemas.fraud_schema import FraudEvaluationRequest
    from backend.app.services.fraud_service import fraud_service
    from backend.app.services.ocr_service import ocr_service

    assert str(ocr_service._reader.device) == "cpu"

    result = fraud_service.evaluate_risk(
        None,
        FraudEvaluationRequest(age=34, declared_income=72000),
    )

    assert result.model_used == "random_forest"
    assert result.top_risk_drivers or result.top_risk_mitigators


def test_opencv_preprocessing_and_rapidfuzz_matching_still_work():
    from backend.app.config import settings
    from backend.app.services.matcher_service import matcher_service
    from backend.app.services.ocr_service import ocr_service

    sample = Path(settings.BASE_DIR) / "data_samples" / "sample_id_john_doe_pass.png"
    image, report = ocr_service.preprocess_image(str(sample))
    match = matcher_service.match_identity(
        "John Doe",
        "SIM-9821-4471",
        "1990-05-14",
        "John Doe",
        "SIM-9821-4471",
        "1990-05-14",
    )

    assert image.ndim == 2
    assert "tamper_suspected" in report
    assert match["is_verified"]
