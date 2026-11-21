import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml_engine.src.explainer import FraudExplainer

def test():
    print("Testing FraudExplainer...")
    explainer = FraudExplainer(model_name="random_forest")
    
    # Sample suspicious applicant profile
    suspicious_profile = {
        "age": 24,
        "declared_income": 45000.0,
        "id_type": "DEMO_NATIONAL_ID",
        "employment_type": "Freelance",
        "channel": "Web",
        "ocr_name_match_score": 0.42,
        "ocr_id_match_score": 0.55,
        "ocr_dob_match_score": 0.0,
        "tampered_document_flag": 1,
        "duplicate_id_count": 2,
        "duplicate_phone_count": 2,
        "duplicate_email_count": 1,
        "ip_risk_score": 0.88,
        "device_reuse_count": 4,
        "disposable_email": 1,
        "registration_velocity": 8,
        "address_mismatch_flag": 1
    }
    
    explanation = explainer.explain_instance(suspicious_profile)
    print("\nTop Risk Drivers (Increasing Fraud Score):")
    for item in explanation["top_risk_drivers"]:
        print(f"  [+] {item['label']}: +{item['shap_value']:.4f}")
        
    print("\nTop Risk Mitigators (Decreasing Fraud Score):")
    for item in explanation["top_risk_mitigators"]:
        print(f"  [-] {item['label']}: {item['shap_value']:.4f}")
        
    print("\nGlobal Feature Importance (Top 5):")
    global_imp = explainer.get_global_feature_importance()
    for item in global_imp[:5]:
        print(f"  * {item['label']}: {item['importance']:.4f}")

if __name__ == "__main__":
    test()

def test_random_forest_explainer():
    explainer = FraudExplainer(model_name="random_forest")
    explanation = explainer.explain_instance({
        "age": 24,
        "declared_income": 45000.0,
        "id_type": "DEMO_NATIONAL_ID",
        "employment_type": "Freelance",
        "channel": "Web",
        "ocr_name_match_score": 0.42,
        "ocr_id_match_score": 0.55,
        "ocr_dob_match_score": 0.0,
        "tampered_document_flag": 1,
        "duplicate_id_count": 2,
        "duplicate_phone_count": 2,
        "duplicate_email_count": 1,
        "ip_risk_score": 0.88,
        "device_reuse_count": 4,
        "disposable_email": 1,
        "registration_velocity": 8,
        "address_mismatch_flag": 1
    })
    assert "top_risk_drivers" in explanation
