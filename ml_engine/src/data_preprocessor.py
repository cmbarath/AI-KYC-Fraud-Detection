import os
import joblib
import pandas as pd
from typing import Tuple, List
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

NUMERICAL_FEATURES: List[str] = [
    "age",
    "declared_income",
    "ocr_name_match_score",
    "ocr_id_match_score",
    "ocr_dob_match_score",
    "tampered_document_flag",
    "duplicate_id_count",
    "duplicate_phone_count",
    "duplicate_email_count",
    "ip_risk_score",
    "device_reuse_count",
    "disposable_email",
    "registration_velocity",
    "address_mismatch_flag"
]

CATEGORICAL_FEATURES: List[str] = [
    "id_type",
    "employment_type",
    "channel"
]

TARGET_COLUMN: str = "is_fraud"

class KYCDataPreprocessor:
    def __init__(self):
        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), NUMERICAL_FEATURES),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ],
            remainder="drop"
        )
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame) -> "KYCDataPreprocessor":
        X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
        self.preprocessor.fit(X)
        self._set_feature_names()
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fitted:
            raise ValueError("Preprocessor has not been fitted yet.")
        X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
        transformed_array = self.preprocessor.transform(X)
        return pd.DataFrame(transformed_array, columns=self.feature_names, index=df.index)

    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        self.fit(df)
        X_trans = self.transform(df)
        y = df[TARGET_COLUMN] if TARGET_COLUMN in df.columns else None
        return X_trans, y

    def _set_feature_names(self):
        cat_encoder = self.preprocessor.named_transformers_["cat"]
        encoded_cats = list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
        self.feature_names = NUMERICAL_FEATURES + encoded_cats

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "KYCDataPreprocessor":
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Preprocessor file not found at: {filepath}")
        return joblib.load(filepath)
