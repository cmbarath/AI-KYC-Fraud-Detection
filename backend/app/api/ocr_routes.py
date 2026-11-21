import hashlib
import io
import json
import os
import tempfile
import uuid
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session
from storage3.exceptions import StorageApiError
from typing import Optional

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.document import Document
from backend.app.models.kyc_application import KYCApplication
from backend.app.schemas.ocr_schema import (
    DocumentProcessRequest,
    DocumentProcessResponse,
    DocumentUploadAuthorizationRequest,
    DocumentUploadAuthorizationResponse,
    MatchVerifyRequest,
    MatchVerifyResponse,
    OCRExtractResponse,
)
from backend.app.services.matcher_service import matcher_service
from backend.app.services.ocr_service import ocr_service
from backend.app.services.supabase_storage import get_storage_bucket
from backend.app.security import require_application_access

router = APIRouter(
    prefix="/ocr",
    tags=["OCR & Document Processing"],
    dependencies=[Depends(require_application_access)],
)

ALLOWED_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def _validate_filename(filename: Optional[str], content_type: str) -> str:
    if (
        not filename
        or len(filename) > 256
        or "/" in filename
        or "\\" in filename
        or any(ord(char) < 32 for char in filename)
    ):
        raise HTTPException(status_code=400, detail="Invalid document filename.")

    extension = os.path.splitext(filename)[1].lower()
    expected_type = ALLOWED_TYPES.get(extension)
    if expected_type is None or content_type.lower() != expected_type:
        raise HTTPException(
            status_code=400,
            detail="Only matching PNG and JPEG filenames and MIME types are accepted.",
        )
    return extension


def _validate_image_bytes(image_bytes: bytes, content_type: str) -> None:
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")
    if len(image_bytes) > settings.MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 5 MB limit.")

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            actual_type = {
                "JPEG": "image/jpeg",
                "PNG": "image/png",
            }.get(image.format or "")
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid image.") from None

    if actual_type != content_type.lower():
        raise HTTPException(
            status_code=400,
            detail="The image contents do not match the declared MIME type.",
        )


def _validate_object_path(applicant_id: str, object_path: str, extension: str) -> None:
    try:
        applicant_folder = str(UUID(applicant_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid applicant identifier.") from None

    if "\\" in object_path or object_path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid Storage object path.")

    parts = object_path.split("/")
    if len(parts) != 2 or parts[0] != applicant_folder:
        raise HTTPException(status_code=403, detail="Document path does not belong to this applicant.")

    object_name, object_extension = os.path.splitext(parts[1])
    try:
        valid_object_name = str(UUID(object_name)) == object_name
    except ValueError:
        valid_object_name = False
    if not valid_object_name or object_extension.lower() != extension:
        raise HTTPException(status_code=400, detail="Invalid Storage object path.")


def _get_applicant(db: Session, applicant_id: str) -> KYCApplication:
    applicant = (
        db.query(KYCApplication)
        .filter(KYCApplication.id == applicant_id)
        .first()
    )
    if applicant is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return applicant


def _download_object(object_path: str) -> bytes:
    try:
        return get_storage_bucket().download(object_path)
    except StorageApiError as exc:
        if str(exc.status) == "404":
            raise HTTPException(status_code=404, detail="Stored document not found.") from None
        raise HTTPException(status_code=502, detail="Document storage retrieval failed.") from None


def _run_ocr(image_bytes: bytes, extension: str):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            prefix="kyc-ocr-",
            dir=tempfile.gettempdir(),
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write(image_bytes)
        return ocr_service.extract_text_and_entities(temp_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def _persist_document(
    db: Session,
    applicant_id: str,
    document_type: str,
    filename: str,
    object_path: str,
    image_bytes: bytes,
    ocr_result: dict,
    match_result: Optional[dict] = None,
) -> Document:
    file_hash = hashlib.sha256(image_bytes).hexdigest()
    duplicate = (
        db.query(Document)
        .filter(Document.file_hash == file_hash)
        .first()
        is not None
    )

    document = Document(
        applicant_id=applicant_id,
        document_type=document_type,
        file_name=filename,
        file_path=object_path,
        file_hash=file_hash,
        extracted_text=ocr_result["raw_text"],
        extracted_name=ocr_result["extracted_name"],
        extracted_id_number=ocr_result["extracted_id_number"],
        extracted_dob=ocr_result["extracted_dob"],
    )
    verification_notes = ["Duplicate file detected"] if duplicate else []
    if match_result is not None:
        document.name_match_score = match_result["name_match_score"]
        document.id_match_score = match_result["id_match_score"]
        document.dob_match_score = match_result["dob_match_score"]
        document.overall_match_score = match_result["overall_match_score"]
        document.is_verified = match_result["is_verified"]
        if match_result["discrepancies"]:
            verification_notes.extend(match_result["discrepancies"])
        else:
            verification_notes.append("Clean match")
    document.verification_notes = "; ".join(verification_notes) or None

    audit = AuditLog(
        applicant_id=applicant_id,
        event_type="DOCUMENT_PROCESSED_OCR",
        actor="SYSTEM_OCR",
        description=f"OCR processed '{filename}'.",
        metadata_json=json.dumps(
            {
                "file_hash": file_hash,
                "is_duplicate": duplicate,
                "object_path": object_path,
            }
        ),
    )
    db.add_all([document, audit])
    try:
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        raise
    return document


def _ocr_response(document_id: Optional[str], filename: str, result: dict):
    return OCRExtractResponse(
        document_id=document_id,
        file_name=filename,
        raw_text=result["raw_text"],
        extracted_name=result["extracted_name"],
        extracted_id_number=result["extracted_id_number"],
        extracted_dob=result["extracted_dob"],
        quality_report=result["quality_report"],
        bounding_boxes=result["bounding_boxes"],
    )


@router.post(
    "/upload-authorization",
    response_model=DocumentUploadAuthorizationResponse,
)
def request_document_upload_authorization(
    req: DocumentUploadAuthorizationRequest,
    db: Session = Depends(get_db),
):
    applicant = _get_applicant(db, req.applicant_id)
    if req.file_size > settings.MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds the 5 MB limit.")

    extension = _validate_filename(req.filename, req.content_type)
    object_path = f"{UUID(applicant.id)}/{uuid.uuid4()}{extension}"
    try:
        signed_upload = get_storage_bucket().create_signed_upload_url(object_path)
    except StorageApiError:
        raise HTTPException(status_code=502, detail="Document upload authorization failed.") from None

    return DocumentUploadAuthorizationResponse(
        bucket=settings.SUPABASE_STORAGE_BUCKET,
        object_path=object_path,
        token=signed_upload["token"],
        expires_in=7200,
        content_type=req.content_type,
        filename=req.filename,
    )


@router.post("/process-upload", response_model=DocumentProcessResponse)
def process_uploaded_document(
    req: DocumentProcessRequest,
    db: Session = Depends(get_db),
):
    applicant = _get_applicant(db, req.applicant_id)
    extension = _validate_filename(req.filename, req.content_type)
    _validate_object_path(applicant.id, req.object_path, extension)

    image_bytes = _download_object(req.object_path)
    _validate_image_bytes(image_bytes, req.content_type)
    try:
        ocr_result = _run_ocr(image_bytes, extension)
    except Exception:
        raise HTTPException(status_code=500, detail="Document OCR processing failed.") from None

    match_result = matcher_service.match_identity(
        form_name=req.form_name,
        form_id=req.form_id,
        form_dob=req.form_dob,
        extracted_name=ocr_result["extracted_name"] or "",
        extracted_id=ocr_result["extracted_id_number"] or "",
        extracted_dob=ocr_result["extracted_dob"] or "",
        raw_ocr_text=ocr_result["raw_text"] or "",
    )
    document = _persist_document(
        db=db,
        applicant_id=applicant.id,
        document_type=req.document_type,
        filename=req.filename,
        object_path=req.object_path,
        image_bytes=image_bytes,
        ocr_result=ocr_result,
        match_result=match_result,
    )

    return DocumentProcessResponse(
        **_ocr_response(document.id, req.filename, ocr_result).model_dump(),
        **match_result,
    )


@router.post("/upload", response_model=OCRExtractResponse)
async def upload_and_extract_document(
    file: UploadFile = File(...),
    applicant_id: Optional[str] = Form(None),
    document_type: Optional[str] = Form("DEMO_ID_FRONT"),
    db: Session = Depends(get_db),
):
    if (
        not settings.ENABLE_LEGACY_DOCUMENT_UPLOAD
        or os.getenv("VERCEL") == "1"
    ):
        raise HTTPException(
            status_code=410,
            detail="Legacy multipart uploads are disabled; use signed Storage uploads.",
        )

    filename = file.filename
    content_type = file.content_type or ""
    extension = _validate_filename(filename, content_type)
    if document_type not in {"DEMO_ID_FRONT", "DEMO_ID_BACK", "DEMO_ADDRESS_PROOF"}:
        raise HTTPException(status_code=400, detail="Invalid document type.")

    image_bytes = await file.read(settings.MAX_DOCUMENT_SIZE_BYTES + 1)
    _validate_image_bytes(image_bytes, content_type)

    object_path = None
    if applicant_id:
        applicant = _get_applicant(db, applicant_id)
        object_path = f"{UUID(applicant.id)}/{uuid.uuid4()}{extension}"
        try:
            get_storage_bucket().upload(
                object_path,
                image_bytes,
                file_options={"content-type": content_type},
            )
        except StorageApiError:
            raise HTTPException(status_code=502, detail="Document storage upload failed.") from None

    try:
        ocr_result = _run_ocr(image_bytes, extension)
    except Exception:
        raise HTTPException(status_code=500, detail="Document OCR processing failed.") from None

    document_id = None
    if applicant_id and object_path:
        document = _persist_document(
            db=db,
            applicant_id=applicant_id,
            document_type=document_type,
            filename=filename,
            object_path=object_path,
            image_bytes=image_bytes,
            ocr_result=ocr_result,
        )
        document_id = document.id

    return _ocr_response(document_id, filename, ocr_result)


@router.get("/documents/{document_id}")
def retrieve_document(
    document_id: str,
    applicant_id: str = Query(...),
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.applicant_id == applicant_id,
        )
        .first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    extension = _validate_filename(
        document.file_name,
        ALLOWED_TYPES.get(os.path.splitext(document.file_name)[1].lower(), ""),
    )
    _validate_object_path(document.applicant_id, document.file_path, extension)
    image_bytes = _download_object(document.file_path)
    _validate_image_bytes(image_bytes, ALLOWED_TYPES[extension])
    return Response(
        content=image_bytes,
        media_type=ALLOWED_TYPES[extension],
        headers={
            "Content-Disposition": (
                "attachment; filename*=UTF-8''"
                + quote(Path(document.file_name).name)
            )
        },
    )


@router.post("/match-verify", response_model=MatchVerifyResponse)
def verify_document_match(
    req: MatchVerifyRequest,
    db: Session = Depends(get_db),
):
    match_result = matcher_service.match_identity(
        form_name=req.form_name,
        form_id=req.form_id,
        form_dob=req.form_dob,
        extracted_name=req.extracted_name or "",
        extracted_id=req.extracted_id or "",
        extracted_dob=req.extracted_dob or "",
        raw_ocr_text=req.raw_text or "",
    )

    if req.applicant_id:
        document = (
            db.query(Document)
            .filter(Document.applicant_id == req.applicant_id)
            .order_by(Document.created_at.desc())
            .first()
        )
        if document:
            document.name_match_score = match_result["name_match_score"]
            document.id_match_score = match_result["id_match_score"]
            document.dob_match_score = match_result["dob_match_score"]
            document.overall_match_score = match_result["overall_match_score"]
            document.is_verified = match_result["is_verified"]
            document.verification_notes = (
                "; ".join(match_result["discrepancies"])
                if match_result["discrepancies"]
                else "Clean match"
            )
            db.commit()

    return MatchVerifyResponse(**match_result)
