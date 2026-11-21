import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.services.ocr_service import ocr_service
from backend.app.services.matcher_service import matcher_service

def test():
    sample_img = os.path.join(PROJECT_ROOT, "data_samples", "sample_id_john_doe_pass.png")
    print(f"Testing OCR on: {sample_img}")
    
    ocr_result = ocr_service.extract_text_and_entities(sample_img)
    print("\nOCR Extraction Output:")
    print("Extracted Name:", ocr_result["extracted_name"])
    print("Extracted ID:", ocr_result["extracted_id_number"])
    print("Extracted DOB:", ocr_result["extracted_dob"])
    print("Quality Report:", ocr_result["quality_report"])

    # Test Matching with declared form data
    form_data = {
        "form_name": "Johnathan Doe",
        "form_id": "SIM-9821-4471",
        "form_dob": "1990-05-14"
    }

    match_result = matcher_service.match_identity(
        form_name=form_data["form_name"],
        form_id=form_data["form_id"],
        form_dob=form_data["form_dob"],
        extracted_name=ocr_result["extracted_name"] or "",
        extracted_id=ocr_result["extracted_id_number"] or "",
        extracted_dob=ocr_result["extracted_dob"] or "",
        raw_ocr_text=ocr_result["raw_text"]
    )

    print("\nMatching Cross-Validation Results:")
    print("Name Match Score:", match_result["name_match_score"])
    print("ID Match Score:", match_result["id_match_score"])
    print("DOB Match Score:", match_result["dob_match_score"])
    print("Overall Score:", match_result["overall_match_score"])
    print("Is Verified:", match_result["is_verified"])

if __name__ == "__main__":
    test()

def test_ocr_pipeline():
    test()
