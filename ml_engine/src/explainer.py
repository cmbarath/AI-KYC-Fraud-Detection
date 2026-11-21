import os
import sys
import joblib
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import shap
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from ml_engine.src.data_preprocessor import KYCDataPreprocessor

FEATURE_LABEL_MAP = {
    "age": "Applicant Age",
    "declared_income": "Declared Annual Income",
    "ocr_name_match_score": "OCR Name Similarity",
    "ocr_id_match_score": "OCR ID Number Match",
    "ocr_dob_match_score": "OCR DOB Match",
    "tampered_document_flag": "Document Tampering Flag",
    "duplicate_id_count": "Reused ID Number Count",
    "duplicate_phone_count": "Reused Phone Number Count",
    "duplicate_email_count": "Reused Email Domain/Address Count",
    "ip_risk_score": "IP Reputation Risk Score",
    "device_reuse_count": "Device Fingerprint Reuse",
    "disposable_email": "Disposable/Temporary Email",
    "registration_velocity": "Rapid Application Velocity",
    "address_mismatch_flag": "Declared vs Geolocation Mismatch",
    "id_type_DEMO_NATIONAL_ID": "ID Type: Demo National ID",
    "id_type_DEMO_PASSPORT": "ID Type: Demo Passport",
    "id_type_DEMO_DRIVERS_LICENSE": "ID Type: Demo Drivers License",
    "employment_type_Salaried": "Employment: Salaried",
    "employment_type_Self-Employed": "Employment: Self-Employed",
    "employment_type_Freelance": "Employment: Freelance",
    "employment_type_Student": "Employment: Student",
    "employment_type_Unemployed": "Employment: Unemployed",
    "channel_Web": "Application Channel: Web",
    "channel_Mobile_App": "Application Channel: Mobile App",
    "channel_Partner_Agent": "Application Channel: Partner Agent"
}

class FraudExplainer:
    def __init__(self, model_name: str = "xgboost"):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "saved_models"))
        preprocessor_path = os.path.join(base_dir, "preprocessor.joblib")
        model_path = os.path.join(base_dir, f"{model_name.lower()}_model.joblib")
        
        self.preprocessor = KYCDataPreprocessor.load(preprocessor_path)
        self.model = joblib.load(model_path)
        self.feature_names = self.preprocessor.feature_names

        # TreeExplainer works directly on tree models (XGBoost / Random Forest)
        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            # Fallback for linear or complex models
            self.explainer = shap.Explainer(self.model)

    def explain_instance(self, input_dict: Dict[str, Any], top_n: int = 5) -> Dict[str, Any]:
        """
        Explains a single prediction instance using SHAP.
        Returns top risk-increasing drivers and top risk-reducing mitigators.
        """
        df_single = pd.DataFrame([input_dict])
        X_trans = self.preprocessor.transform(df_single)
        
        shap_vals = self.explainer(X_trans)
        
        # Handle SHAP output shapes
        if hasattr(shap_vals, "values"):
            values = shap_vals.values[0]
            # Binary classification: check if multi-class dimension exists
            if len(values.shape) > 1 and values.shape[-1] == 2:
                values = values[:, 1]
        else:
            values = np.array(shap_vals)[0]

        contributions = []
        for feat_name, shap_val, orig_val in zip(self.feature_names, values, X_trans.values[0]):
            friendly_name = FEATURE_LABEL_MAP.get(feat_name, feat_name)
            contributions.append({
                "feature": feat_name,
                "label": friendly_name,
                "shap_value": float(round(shap_val, 4)),
                "transformed_value": float(round(orig_val, 4)),
                "direction": "RISK_INCREASE" if shap_val > 0 else "RISK_DECREASE"
            })

        # Sort by absolute impact
        contributions_sorted = sorted(contributions, key=lambda x: abs(x["shap_value"]), reverse=True)
        top_risk_drivers = [c for c in contributions_sorted if c["direction"] == "RISK_INCREASE"][:top_n]
        top_risk_mitigators = [c for c in contributions_sorted if c["direction"] == "RISK_DECREASE"][:top_n]

        return {
            "all_contributions": contributions,
            "top_risk_drivers": top_risk_drivers,
            "top_risk_mitigators": top_risk_mitigators
        }

    def get_global_feature_importance(self) -> List[Dict[str, Any]]:
        """Returns feature importance ranking for the model."""
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            ranked = []
            for feat, imp in zip(self.feature_names, importances):
                ranked.append({
                    "feature": feat,
                    "label": FEATURE_LABEL_MAP.get(feat, feat),
                    "importance": float(round(imp, 4))
                })
            ranked.sort(key=lambda x: x["importance"], reverse=True)
            return ranked
        return []
