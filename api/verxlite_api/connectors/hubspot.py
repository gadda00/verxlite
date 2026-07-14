"""
HubSpot Connector
"""

from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timedelta, timezone

from verxlite_api.config import settings
from verxlite_api.db.session import session
from verxlite_api.models.connection import Connection
from verxlite_api.utils.logger import get_logger
from verxlite_api.utils.encryption import encrypt_data, decrypt_data

logger = get_logger("hubspot_connector")


class HubSpotConnector:
    """
    Connector for HubSpot CRM.
    """

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, connection_id: str, tenant_id: Optional[str] = None):
        self.db = session()
        self.connection = self._get_connection(connection_id, tenant_id)
        self.access_token = self._get_access_token()

    def _get_connection(self, connection_id: str, tenant_id: Optional[str] = None) -> Connection:
        query = self.db.query(Connection).filter(
            Connection.id == connection_id,
            Connection.provider == "hubspot",
        )
        if tenant_id is not None:
            query = query.filter(Connection.tenant_id == tenant_id)
        connection = query.first()
        if not connection:
            raise ValueError(f"HubSpot connection not found: {connection_id}")
        return connection

    def _get_access_token(self) -> str:
        if not self.connection.access_token:
            raise ValueError("No access token for this connection")
        return decrypt_data(self.connection.access_token)

    async def _refresh_access_token(self) -> str:
        if not self.connection.refresh_token:
            raise ValueError("No refresh token for this connection")

        refresh_token = decrypt_data(self.connection.refresh_token)
        data = {
            "grant_type": "refresh_token",
            "client_id": settings.HUBSPOT_CLIENT_ID,
            "client_secret": settings.HUBSPOT_CLIENT_SECRET,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/oauth/v1/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()
            new_access_token = token_data["access_token"]
            new_expires_in = int(token_data.get("expires_in", 21600))

            self.connection.access_token = encrypt_data(new_access_token)
            self.connection.expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=max(new_expires_in - 60, 60)
            )
            self.db.commit()
            self.access_token = new_access_token
            return new_access_token

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=self._get_headers(), **kwargs)
            if response.status_code == 401:
                await self._refresh_access_token()
                response = await client.request(
                    method, url, headers=self._get_headers(), **kwargs
                )
            return response

    async def get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/crm/v3/objects/contacts"
        params = {"q": email}
        response = await self._request("GET", url, params=params)
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise ValueError(f"Failed to get contact: {response.status_code}")
        results = response.json().get("results", [])
        return results[0] if results else None

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        response = await self._request("GET", url)
        if response.status_code != 200:
            raise ValueError(f"Failed to get contact: {response.status_code}")
        return response.json()

    async def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        **properties,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/crm/v3/objects/contacts"
        payload = {
            "properties": {
                "email": email,
                "firstname": first_name,
                "lastname": last_name,
                "company": company,
                **properties,
            }
        }
        response = await self._request("POST", url, json=payload)
        if response.status_code != 201:
            raise ValueError(f"Failed to create contact: {response.status_code}")
        return response.json()

    async def update_contact(self, contact_id: str, **properties) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        payload = {"properties": properties}
        response = await self._request("PATCH", url, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to update contact: {response.status_code}")
        return response.json()

    async def create_note(self, contact_id: str, body: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/crm/v3/objects/notes"
        payload = {
            "properties": {
                "hs_note_body": body,
                "hs_associated_object_id": contact_id,
                "hs_associated_object_type": "CONTACT",
            }
        }
        response = await self._request("POST", url, json=payload)
        if response.status_code != 201:
            raise ValueError(f"Failed to create note: {response.status_code}")
        return response.json()

    async def create_task(
        self,
        contact_id: str,
        title: str,
        due_date: Optional[str] = None,
        body: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/crm/v3/objects/tasks"
        payload = {
            "properties": {
                "hs_task_subject": title,
                "hs_task_body": body or "",
                "hs_associated_object_id": contact_id,
                "hs_associated_object_type": "CONTACT",
            }
        }
        if due_date:
            payload["properties"]["hs_task_due_date"] = due_date
        response = await self._request("POST", url, json=payload)
        if response.status_code != 201:
            raise ValueError(f"Failed to create task: {response.status_code}")
        return response.json()

    async def update_deal_stage(self, deal_id: str, stage: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/crm/v3/objects/deals/{deal_id}"
        payload = {"properties": {"dealstage": stage}}
        response = await self._request("PATCH", url, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to update deal stage: {response.status_code}")
        return response.json()
