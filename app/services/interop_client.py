# app/services/interop_client.py
import os
import httpx

class ReservationServiceClient:
    def __init__(self):
        self.base_url = os.getenv("RESERVATION_SERVICE_URL")

    async def get_reservations_for_employee(self, employee_id: int):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/reservations", params={"employee_id": employee_id})
            r.raise_for_status()
            return r.json()
