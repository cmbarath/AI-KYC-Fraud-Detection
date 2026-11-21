from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class QualityReport(BaseModel):
    laplacian_variance: float
    is_blurry: bool
    edge_density: float
    tamper_suspected: bool

class BoundingBox(BaseModel):
    box: List[List[int]]
    text: str
    confidence: float

class OCRExtractResponse(BaseModel):
    document_id: Optional[str] = None
    file_name: str
    raw_text: str
    extracted_name: Optional[str]
    extracted_id_number: Optional[str]
    extracted_dob: Optional[str]
    quality_report: QualityReport
    bounding_boxes: List[BoundingBox]

class MatchVerifyRequest(BaseModel):
    applicant_id: Optional[str] = None
    form_name: str
    form_id: str
    form_dob: str
    extracted_name: Optional[str] = None
    extracted_id: Optional[str] = None
    extracted_dob: Optional[str] = None
    raw_text: Optional[str] = ""

class MatchVerifyResponse(BaseModel):
    name_match_score: float
    id_match_score: float
    dob_match_score: float
    overall_match_score: float
    is_verified: bool
    discrepancies: List[str]


class DocumentUploadAuthorizationRequest(BaseModel):
    applicant_id: str
    filename: str
    content_type: Literal["image/jpeg", "image/png"]
    file_size: int = Field(gt=0)
    document_type: Literal[
        "DEMO_ID_FRONT",
        "DEMO_ID_BACK",
        "DEMO_ADDRESS_PROOF"
    ] = "DEMO_ID_FRONT"


class DocumentUploadAuthorizationResponse(BaseModel):
    bucket: str
    object_path: str
    token: str
    expires_in: int
    content_type: str
    filename: str


class DocumentProcessRequest(BaseModel):
    applicant_id: str
    object_path: str
    filename: str
    content_type: Literal["image/jpeg", "image/png"]
    document_type: Literal[
        "DEMO_ID_FRONT",
        "DEMO_ID_BACK",
        "DEMO_ADDRESS_PROOF"
    ] = "DEMO_ID_FRONT"
    form_name: str
    form_id: str
    form_dob: str


class DocumentProcessResponse(OCRExtractResponse):
    name_match_score: float
    id_match_score: float
    dob_match_score: float
    overall_match_score: float
    is_verified: bool
    discrepancies: List[str]
