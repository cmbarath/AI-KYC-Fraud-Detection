import os
import requests
import base64
import json
import mimetypes
from typing import Dict, Any, Optional
from urllib.parse import urlsplit, urlunsplit

from supabase import create_client

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1"


def _streamlit_secret(name: str) -> Optional[str]:
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError
    except ImportError:
        return None

    try:
        value = st.secrets.get(name)
    except StreamlitSecretNotFoundError:
        return None
    return str(value) if value else None


def _configured_value(name: str) -> Optional[str]:
    return os.getenv(name) or _streamlit_secret(name)

class APIClient:
    def __init__(self, base_url: Optional[str] = None):
        configured_url = base_url or _configured_value("BACKEND_API_URL")
        self.base_url = (configured_url or DEFAULT_API_BASE_URL).rstrip("/")

    @property
    def health_url(self) -> Optional[str]:
        try:
            parsed = urlsplit(self.base_url)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.query
                or parsed.fragment
            ):
                return None

            hostname = parsed.hostname
            if ":" in hostname:
                hostname = f"[{hostname}]"
            if parsed.port is not None:
                hostname = f"{hostname}:{parsed.port}"

            path_segments = [segment for segment in parsed.path.split("/") if segment]
            while path_segments and path_segments[-1] == "health":
                path_segments.pop()
            path = "/" + "/".join(path_segments + ["health"])
            return urlunsplit((parsed.scheme, hostname, path, "", ""))
        except ValueError:
            return None

    @staticmethod
    def _access_token(name: str) -> str:
        token = _configured_value(name)

        if not token:
            raise RuntimeError(f"Configure {name} in the Streamlit secrets.")
        return token

    def _application_headers(self) -> Dict[str, str]:
        return {"X-API-Token": self._access_token("APP_API_TOKEN")}

    @staticmethod
    def _admin_headers(admin_token: str) -> Dict[str, str]:
        if not admin_token:
            raise RuntimeError("Administrator access must be unlocked first.")
        return {"X-Admin-Access-Token": admin_token}

    def check_health(self) -> Dict[str, Any]:
        health_url = self.health_url
        if health_url is None:
            return {
                "status": "offline",
                "diagnostic": (
                    "Invalid BACKEND_API_URL. Configure an HTTP(S) backend base URL "
                    "without query parameters or a fragment."
                ),
            }

        try:
            resp = requests.get(health_url, timeout=20)
        except requests.exceptions.Timeout:
            return {
                "status": "offline",
                "diagnostic": (
                    "The health check timed out after 20 seconds. The backend may "
                    "still be starting or may be temporarily overloaded."
                ),
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "offline",
                "diagnostic": (
                    "Could not connect to the backend. Check the configured URL and "
                    "confirm the service is reachable."
                ),
            }
        except requests.exceptions.RequestException:
            return {
                "status": "offline",
                "diagnostic": (
                    "The health-check request failed. Check the backend URL and "
                    "network access."
                ),
            }

        if resp.status_code != 200:
            return {
                "status": "unhealthy",
                "diagnostic": f"The backend returned HTTP {resp.status_code} for its health check.",
            }

        try:
            result = resp.json()
        except ValueError:
            return {
                "status": "unhealthy",
                "diagnostic": "The backend returned invalid JSON for its health check.",
            }

        if not isinstance(result, dict) or not isinstance(result.get("status"), str):
            return {
                "status": "unhealthy",
                "diagnostic": (
                    "The backend health response did not contain a valid status."
                ),
            }

        result["diagnostic"] = (
            "The backend health check succeeded."
            if result["status"] == "healthy"
            else "The backend responded but is not reporting a healthy status."
        )
        return result

    def register_kyc(self, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/kyc/register",
            json=data,
            headers=self._application_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        applicant_id: Optional[str] = None,
        doc_type: str = "DEMO_ID_FRONT"
    ) -> Dict[str, Any]:
        content_type = mimetypes.guess_type(filename)[0]
        if content_type not in {"image/jpeg", "image/png"}:
            raise ValueError("Only PNG and JPEG identity documents are supported.")
        files = {"file": (filename, file_bytes, content_type)}
        data = {}
        if applicant_id:
            data["applicant_id"] = applicant_id
        data["document_type"] = doc_type

        resp = requests.post(
            f"{self.base_url}/ocr/upload",
            files=files,
            data=data,
            headers=self._application_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def create_document_upload_authorization(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/ocr/upload-authorization",
            json=data,
            headers=self._application_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _frontend_supabase_config(
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ) -> tuple[str, str]:
        if not supabase_url:
            supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_key:
            supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            try:
                import streamlit as st
                from streamlit.errors import StreamlitSecretNotFoundError

                try:
                    supabase_url = supabase_url or st.secrets.get("SUPABASE_URL")
                    supabase_key = (
                        supabase_key
                        or st.secrets.get("SUPABASE_KEY")
                        or st.secrets.get("SUPABASE_ANON_KEY")
                    )
                except StreamlitSecretNotFoundError:
                    pass
            except ImportError:
                pass

        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "Configure SUPABASE_URL and a publishable SUPABASE_KEY in Streamlit secrets."
            )

        parsed = urlsplit(supabase_url.strip())
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path.rstrip("/") not in ("", "/rest/v1")
        ):
            raise RuntimeError("SUPABASE_URL must be the Supabase project URL.")

        if supabase_key.startswith("sb_publishable_"):
            is_publishable = True
        elif supabase_key.startswith("sb_secret_"):
            is_publishable = False
        else:
            try:
                payload = supabase_key.split(".")[1]
                payload += "=" * ((4 - len(payload) % 4) % 4)
                claims = json.loads(base64.urlsafe_b64decode(payload))
                is_publishable = claims.get("role") == "anon"
            except (IndexError, ValueError, json.JSONDecodeError):
                is_publishable = False

        if not is_publishable:
            raise RuntimeError(
                "The Streamlit Storage key must be a publishable or anon key, never a secret key."
            )

        project_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        return project_url, supabase_key

    def upload_to_signed_document_path(
        self,
        authorization: Dict[str, Any],
        file_bytes: bytes,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ) -> None:
        project_url, publishable_key = self._frontend_supabase_config(
            supabase_url,
            supabase_key,
        )
        try:
            client = create_client(project_url, publishable_key)
            client.storage.from_(authorization["bucket"]).upload_to_signed_url(
                authorization["object_path"],
                authorization["token"],
                file_bytes,
                file_options={"content-type": authorization["content_type"]},
            )
        except Exception:
            raise RuntimeError("The direct document upload failed.") from None

    def validate_supabase_upload_config(self) -> None:
        self._frontend_supabase_config()

    def process_uploaded_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/ocr/process-upload",
            json=data,
            headers=self._application_headers(),
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def match_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/ocr/match-verify",
            json=data,
            headers=self._application_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def evaluate_fraud(self, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/fraud/evaluate",
            json=data,
            headers=self._application_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def check_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/transactions/check",
            json=data,
            headers=self._application_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_admin_metrics(self, admin_token: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/admin/metrics",
            headers=self._admin_headers(admin_token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def list_applications(
        self,
        status: str = "ALL",
        search: str = "",
        *,
        admin_token: str,
    ) -> Dict[str, Any]:
        params = {"status": status}
        if search:
            params["search"] = search
        resp = requests.get(
            f"{self.base_url}/admin/applications",
            params=params,
            headers=self._admin_headers(admin_token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_application(self, applicant_id: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/kyc/{applicant_id}",
            headers=self._application_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def lookup_application(self, app_number: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/kyc/lookup/{app_number}",
            headers=self._application_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def update_application_status(
        self,
        applicant_id: str,
        new_status: str,
        notes: str = "",
        *,
        admin_token: str,
    ) -> Dict[str, Any]:
        payload = {"status": new_status, "notes": notes}
        resp = requests.patch(
            f"{self.base_url}/admin/applications/{applicant_id}/status",
            json=payload,
            headers=self._admin_headers(admin_token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_model_benchmarks(self) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/fraud/models",
            headers=self._application_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_feature_importance(self) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/fraud/feature-importance",
            headers=self._application_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_audit_logs(self, applicant_id: str, *, admin_token: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{self.base_url}/admin/audit-logs/{applicant_id}",
            headers=self._admin_headers(admin_token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

api_client = APIClient()
