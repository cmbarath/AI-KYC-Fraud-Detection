"""
Synthetic KYC & Fraud Dataset Generator
Generates realistic, synthetic identity and verification data with simulated fraud vectors.
DOES NOT USE ANY REAL PII. All data is synthetically generated using Faker and NumPy.
"""

import os
import random
import numpy as np
import pandas as pd
from faker import Faker

def generate_synthetic_kyc_data(num_samples: int = 6000, random_seed: int = 42) -> pd.DataFrame:
    np.random.seed(random_seed)
    random.seed(random_seed)
    fake = Faker()

    records = []
    
    # Common disposable email domains for fraud simulation
    disposable_domains = ["mailinator.com", "tempmail.net", "10minutemail.com", "guerrillamail.com", "throwaway.org"]
    legit_domains = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "companycorp.com"]

    for _ in range(num_samples):
        # Determine latent fraud profile (~18% base probability of fraud)
        is_fraud = 1 if np.random.rand() < 0.18 else 0

        # Identity & Demographics
        age = int(np.random.normal(38, 12))
        age = max(18, min(80, age))

        id_type = random.choice(["DEMO_NATIONAL_ID", "DEMO_PASSPORT", "DEMO_DRIVERS_LICENSE"])
        employment_type = random.choice(["Salaried", "Self-Employed", "Freelance", "Student", "Unemployed"])
        channel = random.choice(["Web", "Mobile_App", "Partner_Agent"])
        
        income_base = np.random.lognormal(mean=10.5, sigma=0.6)  # ~35,000 to 150,000
        declared_income = float(round(income_base, -2))

        if is_fraud == 1:
            # Inject fraud behaviors
            fraud_type = random.choice(["id_spoof", "synthetic_id", "bot_velocity", "stolen_credential"])
            
            if fraud_type == "id_spoof":
                ocr_name_match = np.random.uniform(0.15, 0.65)
                ocr_id_match = np.random.uniform(0.20, 0.70)
                ocr_dob_match = np.random.choice([0.0, 1.0], p=[0.7, 0.3])
                tampered_document_flag = np.random.choice([0, 1], p=[0.2, 0.8])
                duplicate_id_count = np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1])
                duplicate_phone_count = np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2])
                duplicate_email_count = np.random.choice([0, 1], p=[0.7, 0.3])
                ip_risk_score = np.random.uniform(0.40, 0.95)
                device_reuse_count = np.random.choice([1, 2, 4, 8], p=[0.3, 0.3, 0.2, 0.2])
                disposable_email = np.random.choice([0, 1], p=[0.4, 0.6])
                registration_velocity = int(np.random.exponential(scale=3)) + 1
                address_mismatch_flag = np.random.choice([0, 1], p=[0.3, 0.7])

            elif fraud_type == "synthetic_id":
                ocr_name_match = np.random.uniform(0.50, 0.85)
                ocr_id_match = np.random.uniform(0.80, 1.0)
                ocr_dob_match = 1.0
                tampered_document_flag = np.random.choice([0, 1], p=[0.6, 0.4])
                duplicate_id_count = np.random.choice([1, 2, 3, 5], p=[0.2, 0.4, 0.2, 0.2])
                duplicate_phone_count = np.random.choice([1, 2, 4], p=[0.3, 0.4, 0.3])
                duplicate_email_count = np.random.choice([1, 2, 3], p=[0.3, 0.4, 0.3])
                ip_risk_score = np.random.uniform(0.60, 0.99)
                device_reuse_count = np.random.choice([2, 5, 9], p=[0.3, 0.4, 0.3])
                disposable_email = np.random.choice([0, 1], p=[0.3, 0.7])
                registration_velocity = np.random.randint(2, 10)
                address_mismatch_flag = np.random.choice([0, 1], p=[0.4, 0.6])

            elif fraud_type == "bot_velocity":
                ocr_name_match = np.random.uniform(0.85, 1.0)
                ocr_id_match = np.random.uniform(0.85, 1.0)
                ocr_dob_match = 1.0
                tampered_document_flag = 0
                duplicate_id_count = 0
                duplicate_phone_count = np.random.choice([0, 1, 3], p=[0.4, 0.3, 0.3])
                duplicate_email_count = np.random.choice([0, 1, 2], p=[0.4, 0.4, 0.2])
                ip_risk_score = np.random.uniform(0.70, 0.99)
                device_reuse_count = np.random.randint(4, 15)
                disposable_email = np.random.choice([0, 1], p=[0.2, 0.8])
                registration_velocity = np.random.randint(6, 25)
                address_mismatch_flag = np.random.choice([0, 1], p=[0.5, 0.5])

            else: # stolen_credential
                ocr_name_match = np.random.uniform(0.90, 1.0)
                ocr_id_match = np.random.uniform(0.90, 1.0)
                ocr_dob_match = 1.0
                tampered_document_flag = np.random.choice([0, 1], p=[0.8, 0.2])
                duplicate_id_count = np.random.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
                duplicate_phone_count = np.random.choice([1, 2, 4], p=[0.4, 0.4, 0.2])
                duplicate_email_count = np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2])
                ip_risk_score = np.random.uniform(0.55, 0.95)
                device_reuse_count = np.random.choice([1, 3, 6], p=[0.4, 0.3, 0.3])
                disposable_email = np.random.choice([0, 1], p=[0.5, 0.5])
                registration_velocity = np.random.randint(1, 5)
                address_mismatch_flag = np.random.choice([0, 1], p=[0.2, 0.8])

        else:
            # Normal legitimate applicant behaviors
            # Introduce realistic edge cases (e.g. slight OCR typos, shared IP at offices)
            has_typo = np.random.rand() < 0.12
            ocr_name_match = float(np.clip(np.random.normal(0.82 if has_typo else 0.95, 0.08), 0.50, 1.0))
            ocr_id_match = float(np.clip(np.random.normal(0.94, 0.06), 0.65, 1.0))
            ocr_dob_match = 1.0 if np.random.rand() > 0.08 else 0.0
            tampered_document_flag = 1 if np.random.rand() < 0.04 else 0
            duplicate_id_count = 1 if np.random.rand() < 0.03 else 0
            duplicate_phone_count = 1 if np.random.rand() < 0.08 else 0
            duplicate_email_count = 1 if np.random.rand() < 0.06 else 0
            ip_risk_score = float(np.clip(np.random.beta(2.0, 5.0), 0.05, 0.75))
            device_reuse_count = 1 if np.random.rand() > 0.15 else np.random.choice([2, 3])
            disposable_email = 1 if np.random.rand() < 0.05 else 0
            registration_velocity = 1 if np.random.rand() > 0.10 else np.random.randint(2, 4)
            address_mismatch_flag = 1 if np.random.rand() < 0.15 else 0

        # Inject 3% label noise (simulating labeling ambiguity in real AML/KYC data)
        if np.random.rand() < 0.03:
            is_fraud = 1 - is_fraud

        # Construct email & phone synthetic placeholders
        domain = random.choice(disposable_domains if disposable_email == 1 else legit_domains)
        email = f"user_{random.randint(10000, 99999)}@{domain}"
        phone = f"+1555{random.randint(1000000, 9999999)}"

        records.append({
            "age": age,
            "declared_income": declared_income,
            "id_type": id_type,
            "employment_type": employment_type,
            "channel": channel,
            "ocr_name_match_score": round(float(ocr_name_match), 4),
            "ocr_id_match_score": round(float(ocr_id_match), 4),
            "ocr_dob_match_score": round(float(ocr_dob_match), 4),
            "tampered_document_flag": int(tampered_document_flag),
            "duplicate_id_count": int(duplicate_id_count),
            "duplicate_phone_count": int(duplicate_phone_count),
            "duplicate_email_count": int(duplicate_email_count),
            "ip_risk_score": round(float(ip_risk_score), 4),
            "device_reuse_count": int(device_reuse_count),
            "disposable_email": int(disposable_email),
            "registration_velocity": int(registration_velocity),
            "address_mismatch_flag": int(address_mismatch_flag),
            "is_fraud": int(is_fraud)
        })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "synthetic_kyc_dataset.csv")
    print(f"Generating synthetic KYC fraud dataset...")
    df = generate_synthetic_kyc_data(num_samples=6000, random_seed=42)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} records. Saved to: {output_path}")
    print("Class distribution:")
    print(df["is_fraud"].value_counts(normalize=True))
