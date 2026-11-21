import os
import re
import tempfile
from typing import Dict, Any, List, Tuple

import cv2
import numpy as np

from backend.app.easyocr_compat import import_easyocr

easyocr = import_easyocr()


class OCRService:
    _instance = None
    _reader = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OCRService, cls).__new__(cls)
            # EasyOCR reader initialized once (English, CPU mode by default)
            print("Initializing EasyOCR reader engine...")
            model_storage_directory = None
            if os.environ.get("VERCEL") == "1":
                model_storage_directory = os.path.join(
                    tempfile.gettempdir(),
                    ".EasyOCR",
                )
                os.makedirs(model_storage_directory, exist_ok=True)
            cls._reader = easyocr.Reader(
                ['en'],
                gpu=False,
                model_storage_directory=model_storage_directory,
            )
        return cls._instance

    @staticmethod
    def preprocess_image(image_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Loads and cleans the document image using OpenCV filters.
        Detects potential tampering signs like abnormal blur or gradient discontinuities.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Image could not be read from: {image_path}")

        # Check blurriness / sharpness via Laplacian variance
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < 80.0

        # Enhance contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_gray = clahe.apply(gray)

        # Bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(enhanced_gray, 9, 75, 75)

        # Tamper heuristic check
        # High frequency noise analysis
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.sum(edges > 0) / (gray.shape[0] * gray.shape[1]))
        tamper_suspected = is_blurry or (edge_density > 0.35)

        quality_report = {
            "laplacian_variance": round(laplacian_var, 2),
            "is_blurry": is_blurry,
            "edge_density": round(edge_density, 4),
            "tamper_suspected": tamper_suspected
        }

        return denoised, quality_report

    def extract_text_and_entities(self, image_path: str) -> Dict[str, Any]:
        """
        Performs OCR text extraction and structured parsing of document fields.
        """
        denoised_img, quality = self.preprocess_image(image_path)

        # Run OCR on the processed image first, then retain the original image
        # as a fallback when preprocessing yields no usable text.
        results = self._reader.readtext(denoised_img, detail=1)
        if not results:
            results = self._reader.readtext(image_path, detail=1)
        
        extracted_lines: List[str] = []
        raw_text_parts: List[str] = []
        bounding_boxes = []

        for bbox, text, conf in results:
            cleaned_txt = text.strip()
            if cleaned_txt and conf > 0.20:
                extracted_lines.append(cleaned_txt)
                raw_text_parts.append(cleaned_txt)
                # Store bounding boxes for UI rendering
                bounding_boxes.append({
                    "box": [[int(pt[0]), int(pt[1])] for pt in bbox],
                    "text": cleaned_txt,
                    "confidence": round(float(conf), 2)
                })

        full_raw_text = " \n ".join(extracted_lines)

        # Extract structured entities using heuristic pattern matching
        extracted_name = None
        extracted_id = None
        extracted_dob = None

        for idx, line in enumerate(extracted_lines):
            line_upper = line.upper()
            
            # Check for name indicator
            if "FULL NAME" in line_upper or "NAME" in line_upper:
                # Value could be after colon or on the next line
                if ":" in line:
                    extracted_name = line.split(":")[-1].strip()
                elif idx + 1 < len(extracted_lines):
                    extracted_name = extracted_lines[idx + 1].strip()

            # Check for ID number indicator
            if "ID NO" in line_upper or "NATIONAL ID" in line_upper or "PASSPORT NO" in line_upper:
                if ":" in line:
                    extracted_id = line.split(":")[-1].strip()
                elif idx + 1 < len(extracted_lines):
                    extracted_id = extracted_lines[idx + 1].strip()

            # Check for DOB indicator
            if "DATE OF BIRTH" in line_upper or "DOB" in line_upper:
                if ":" in line:
                    extracted_dob = line.split(":")[-1].strip()
                elif idx + 1 < len(extracted_lines):
                    extracted_dob = extracted_lines[idx + 1].strip()

        # Regex fallback for ID pattern (e.g. SIM-XXXX-XXXX or alphanumeric ID)
        if not extracted_id:
            id_match = re.search(r"SIM[-\s]?\d{4}[-\s]?\d{4}", full_raw_text, re.IGNORECASE)
            if id_match:
                extracted_id = id_match.group(0).replace(" ", "-")

        # Regex fallback for DOB pattern (YYYY-MM-DD or DD/MM/YYYY)
        if not extracted_dob:
            dob_match = re.search(r"\b(19\d{2}|20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", full_raw_text)
            if dob_match:
                extracted_dob = dob_match.group(0).replace("/", "-").replace(".", "-")

        return {
            "raw_text": full_raw_text,
            "extracted_name": extracted_name,
            "extracted_id_number": extracted_id,
            "extracted_dob": extracted_dob,
            "bounding_boxes": bounding_boxes,
            "quality_report": quality
        }

ocr_service = OCRService()
