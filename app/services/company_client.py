# app/services/company_client.py
import os
from typing import Optional, Dict, Any, List, Set
import httpx

def _get_bool(env: str, default: bool) -> bool:
    v = os.getenv(env)
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "yes", "y", "on")

class CompanyServiceClient:
    """
    Minimal client for Company Service for read-only lookups & validation.
    Graceful if COMPANY_SERVICE_URL is absent (validation skipped).
    """
    def __init__(self):
        self.base_url = os.getenv("COMPANY_SERVICE_URL", "").rstrip("/")
        self.strict = _get_bool("COMPANY_VALIDATION_STRICT", False)
        if not self.base_url:
            self._enabled = False
            return

        connect_timeout = float(os.getenv("COMPANY_HTTP_CONNECT_TIMEOUT", "2.0"))
        read_timeout = float(os.getenv("COMPANY_HTTP_READ_TIMEOUT", "2.0"))
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=connect_timeout,
                read=read_timeout,
                write=read_timeout,
                pool=connect_timeout,
            ),
        )
        self._enabled = True

    def enabled(self) -> bool:
        return self._enabled

    # ─── Raw calls ────────────────────────────────────────────────────────────

    def get_company(self, company_id: int) -> Optional[Dict[str, Any]]:
        if not self._enabled:
            return None
        try:
            r = self._client.get(f"/companies/{company_id}")
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception:
            if self.strict:
                raise
            return None

    def get_location(self, location_id: int) -> Optional[Dict[str, Any]]:
        if not self._enabled:
            return None
        try:
            r = self._client.get(f"/locations/{location_id}")
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception:
            if self.strict:
                raise
            return None

    def get_services_for_company(self, company_id: int) -> List[Dict[str, Any]]:
        if not self._enabled:
            return []
        try:
            r = self._client.get(f"/services/company/{company_id}")
            r.raise_for_status()
            return r.json()
        except Exception:
            if self.strict:
                raise
            return []

    def get_business_hours_by_company(self, company_id: int) -> List[Dict[str, Any]]:
        if not self._enabled:
            return []
        # If you exposed /business-hours/company/{companyId} in Company svc, use it
        try:
            r = self._client.get(f"/business-hours/company/{company_id}")
            if r.status_code == 404:
                return []
            r.raise_for_status()
            return r.json()
        except Exception:
            if self.strict:
                raise
            return []

    # ─── Helpers for validation ──────────────────────────────────────────────

    def validate_company(self, company_id: Optional[int]) -> bool:
        if company_id is None or not self._enabled:
            return True
        return self.get_company(company_id) is not None

    def validate_location(self, location_id: Optional[int]) -> bool:
        if location_id is None or not self._enabled:
            return True
        return self.get_location(location_id) is not None

    def services_set_for_company(self, company_id: Optional[int]) -> Set[int]:
        if company_id is None or not self._enabled:
            return set()
        return {int(s["id"]) for s in self.get_services_for_company(company_id) if "id" in s}
