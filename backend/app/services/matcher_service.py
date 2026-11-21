import re
from rapidfuzz import fuzz
from typing import Dict, Any

class MatcherService:
    @staticmethod
    def normalize_string(text: str) -> str:
        if not text:
            return ""
        # Remove special characters, multiple spaces, and convert to uppercase
        cleaned = re.sub(r"[^A-Za-z0-9\s]", " ", text)
        return " ".join(cleaned.upper().split())

    @staticmethod
    def normalize_id(id_str: str) -> str:
        if not id_str:
            return ""
        # Remove dashes, spaces for direct alphanumeric comparison
        return re.sub(r"[\s\-_]", "", id_str).upper()

    def match_identity(
        self,
        form_name: str,
        form_id: str,
        form_dob: str,
        extracted_name: str,
        extracted_id: str,
        extracted_dob: str,
        raw_ocr_text: str = ""
    ) -> Dict[str, Any]:
        """
        Cross-validates declared form information against extracted document values
        using fuzzy string matching. Returns granular match scores between 0.0 and 1.0.
        """
        # 1. Name Matching
        norm_form_name = self.normalize_string(form_name)
        norm_ocr_name = self.normalize_string(extracted_name)

        if norm_form_name and norm_ocr_name:
            # Token sort ratio handles middle names or swapped first/last name
            name_score = fuzz.token_sort_ratio(norm_form_name, norm_ocr_name) / 100.0
        elif norm_form_name and raw_ocr_text:
            # Fallback: check if name appears somewhere in raw OCR text
            name_score = fuzz.partial_ratio(norm_form_name, self.normalize_string(raw_ocr_text)) / 100.0
        else:
            name_score = 0.0

        # 2. ID Number Matching
        norm_form_id = self.normalize_id(form_id)
        norm_ocr_id = self.normalize_id(extracted_id)

        if norm_form_id and norm_ocr_id:
            if norm_form_id == norm_ocr_id:
                id_score = 1.0
            else:
                id_score = fuzz.ratio(norm_form_id, norm_ocr_id) / 100.0
        elif norm_form_id and raw_ocr_text:
            id_score = 1.0 if norm_form_id in self.normalize_id(raw_ocr_text) else 0.0
        else:
            id_score = 0.0

        # 3. DOB Matching
        dob_score = 0.0
        if form_dob and extracted_dob:
            clean_form_dob = form_dob.strip().replace("/", "-")
            clean_ocr_dob = extracted_dob.strip().replace("/", "-")
            if clean_form_dob == clean_ocr_dob:
                dob_score = 1.0
            elif clean_form_dob in clean_ocr_dob or clean_ocr_dob in clean_form_dob:
                dob_score = 0.90
            else:
                dob_score = fuzz.ratio(clean_form_dob, clean_ocr_dob) / 100.0
        elif form_dob and raw_ocr_text:
            dob_score = 1.0 if form_dob.strip() in raw_ocr_text else 0.0

        # 4. Overall Weighted Consistency Score
        # Name: 40%, ID: 40%, DOB: 20%
        overall_score = round(
            (name_score * 0.40) + (id_score * 0.40) + (dob_score * 0.20),
            4
        )

        is_verified = bool(overall_score >= 0.75 and id_score >= 0.70 and name_score >= 0.60)

        discrepancies = []
        if name_score < 0.70:
            discrepancies.append(f"Name mismatch: Form '{form_name}' vs Document '{extracted_name or 'Not Found'}' (score: {name_score:.2f})")
        if id_score < 0.80:
            discrepancies.append(f"ID mismatch: Form '{form_id}' vs Document '{extracted_id or 'Not Found'}' (score: {id_score:.2f})")
        if dob_score < 0.80:
            discrepancies.append(f"DOB mismatch: Form '{form_dob}' vs Document '{extracted_dob or 'Not Found'}' (score: {dob_score:.2f})")

        return {
            "name_match_score": round(float(name_score), 4),
            "id_match_score": round(float(id_score), 4),
            "dob_match_score": round(float(dob_score), 4),
            "overall_match_score": float(overall_score),
            "is_verified": is_verified,
            "discrepancies": discrepancies
        }

matcher_service = MatcherService()
