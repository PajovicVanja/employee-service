# app/services/faas_client.py
import os
from typing import Any, Dict, List, Optional, Union
import httpx
from datetime import time as dtime

def _get_bool(env: str, default: bool) -> bool:
    v = os.getenv(env)
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "yes", "y", "on")

def _to_hms(v: Union[str, dtime]) -> str:
    if isinstance(v, dtime):
        return v.strftime("%H:%M:%S")
    return str(v)

class FaaSClient:
    """
    Thin client for the employee FAAS utility.

    - All calls are no-ops when disabled (so service remains self-contained).
    - Fail-open on validation (if FAAS is unreachable, we don't block writes).
    - Accepts FAAS_BASE_URL with or without `/api` and adds it if needed.
    """
    def __init__(self):
        base = (os.getenv("FAAS_BASE_URL", "") or "").rstrip("/")
        self.base_url = base
        self._enabled = _get_bool("FAAS_ENABLED", False) and bool(self.base_url)
        self._audit_enabled = _get_bool("FAAS_AUDIT_ENABLED", False)
        self.service_name = os.getenv("FAAS_AUDIT_SERVICE", "employee-service")

        # Whether we should prefix paths with /api
        self._needs_api_prefix = not self.base_url.endswith("/api")

        if not self._enabled:
            self._client = None
            return

        connect_timeout = float(os.getenv("FAAS_CONNECT_TIMEOUT", "2.0"))
        read_timeout = float(os.getenv("FAAS_READ_TIMEOUT", "2.0"))
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=connect_timeout, read=read_timeout,
                write=read_timeout, pool=connect_timeout
            ),
        )

    # remove the auto '/api' logic completely
    def _path(self, suffix: str) -> str:
        # trust FAAS_BASE_URL exactly
        return suffix if suffix.startswith("/") else f"/{suffix}"

    def enabled(self) -> bool:
        return self._enabled

    # ─── Availability validation ──────────────────────────────────────────────
    def availability_check(
        self,
        slots: List[Dict[str, Any]],
        business_hours: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        slots: [{day_of_week, time_from, time_to, location_id?}] times as str or datetime.time
        business_hours: [{dayNumber, fromTime/timeFrom, toTime/timeTo, ...}] (optional)
        """
        if not self._enabled:
            return {"ok": True, "overlaps": [], "outOfBounds": []}

        payload_slots = []
        for s in slots:
            payload_slots.append({
                "day_of_week": int(s["day_of_week"]),
                "time_from": _to_hms(s["time_from"]),
                "time_to": _to_hms(s["time_to"]),
                "location_id": s.get("location_id"),
            })

        bh = None
        if business_hours:
            bh = []
            for d in business_hours:
                # accept either {fromTime,toTime} or {timeFrom,timeTo}
                from_t = d.get("fromTime", d.get("timeFrom"))
                to_t = d.get("toTime", d.get("timeTo"))
                bh.append({
                    "dayNumber": int(d.get("dayNumber")),
                    "fromTime": _to_hms(from_t),
                    "toTime": _to_hms(to_t),
                })

        try:
            r = self._client.post(self._path("/availability-check"), json={
                "slots": payload_slots,
                "businessHours": bh
            })
            r.raise_for_status()
            return r.json()
        except Exception:
            # Fail-open: don't block writes if FAAS is down.
            return {"ok": True, "overlaps": [], "outOfBounds": []}

    # ─── Audit logging ────────────────────────────────────────────────────────
    def audit(
        self,
        event: str,
        entity_id: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not (self._enabled and self._audit_enabled):
            return
        try:
            self._client.post(self._path("/audit"), json={
                "service": self.service_name,
                "event": event,
                "entityId": entity_id,
                "meta": meta or {}
            })
        except Exception:
            # swallow audit errors (best-effort telemetry)
            pass
