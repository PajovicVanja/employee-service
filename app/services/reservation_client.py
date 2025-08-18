# app/services/reservation_client.py
import os
import httpx

class ReservationServiceClient:
    def __init__(self):
        self.base_url = os.getenv("COMPANY_SERVICE_URL")
        if not self.base_url:
            # If missing, raise so we document a 502 upstream error in the route
            raise RuntimeError("COMPANY_SERVICE_URL is not configured")

    async def get_reservations_for_employee(self, employee_id: int):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/reservations", params={"employee_id": employee_id})
            r.raise_for_status()
            return r.json()
