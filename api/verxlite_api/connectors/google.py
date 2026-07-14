"""
Google Connector
"""

from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timedelta, timezone

from verxlite_api.config import settings
from verxlite_api.db.session import session
from verxlite_api.models.connection import Connection
from verxlite_api.utils.logger import get_logger
from verxlite_api.utils.encryption import encrypt_data, decrypt_data

logger = get_logger("google_connector")


class GoogleConnector:
    """
    Connector for Google Workspace (Gmail, Calendar, Drive).
    """

    BASE_URLS = {
        "gmail": "https://gmail.googleapis.com",
        "calendar": "https://www.googleapis.com/calendar/v3",
        "drive": "https://www.googleapis.com/drive/v3",
    }

    def __init__(self, connection_id: str, tenant_id: Optional[str] = None):
        self.db = session()
        self.connection = self._get_connection(connection_id, tenant_id)
        self.access_token = self._get_access_token()

    def _get_connection(self, connection_id: str, tenant_id: Optional[str] = None) -> Connection:
        """Get the Google connection from the database (scoped to tenant)."""
        query = self.db.query(Connection).filter(
            Connection.id == connection_id,
            Connection.provider == "google",
        )
        if tenant_id is not None:
            query = query.filter(Connection.tenant_id == tenant_id)
        connection = query.first()

        if not connection:
            raise ValueError(f"Google connection not found: {connection_id}")
        return connection

    def _get_access_token(self) -> str:
        """Get the decrypted access token."""
        if not self.connection.access_token:
            raise ValueError("No access token for this connection")
        return decrypt_data(self.connection.access_token)

    async def _refresh_access_token(self) -> str:
        """Refresh the access token if expired."""
        if not self.connection.refresh_token:
            raise ValueError("No refresh token for this connection")

        refresh_token = decrypt_data(self.connection.refresh_token)

        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data=data,
            )
            response.raise_for_status()
            token_data = response.json()
            new_access_token = token_data["access_token"]
            new_expires_in = int(token_data.get("expires_in", 3600))

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
        """Issue a request, refreshing the token once on 401."""
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=self._get_headers(), **kwargs)
            if response.status_code == 401:
                # Token expired, refresh and retry once.
                await self._refresh_access_token()
                response = await client.request(
                    method, url, headers=self._get_headers(), **kwargs
                )
            return response

    async def get_calendar_event(self, event_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URLS['calendar']}/calendars/primary/events/{event_id}"
        response = await self._request("GET", url)
        if response.status_code != 200:
            raise ValueError(f"Failed to get calendar event: {response.status_code}")
        return response.json()

    async def list_calendar_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URLS['calendar']}/calendars/primary/events"
        params: Dict[str, Any] = {"maxResults": max_results}
        if time_min:
            params["timeMin"] = time_min.isoformat() + "Z"
        if time_max:
            params["timeMax"] = time_max.isoformat() + "Z"
        response = await self._request("GET", url, params=params)
        if response.status_code != 200:
            raise ValueError(f"Failed to list calendar events: {response.status_code}")
        return response.json().get("items", [])

    async def get_email_thread(self, thread_id: str) -> Dict[str, Any]:
        url = f"{self.BASE_URLS['gmail']}/gmail/v1/users/me/threads/{thread_id}"
        response = await self._request("GET", url)
        if response.status_code != 200:
            raise ValueError(f"Failed to get email thread: {response.status_code}")
        return response.json()

    async def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URLS['gmail']}/gmail/v1/users/me/messages"
        params = {"q": query, "maxResults": max_results}
        response = await self._request("GET", url, params=params)
        if response.status_code != 200:
            raise ValueError(f"Failed to search emails: {response.status_code}")
        return response.json().get("messages", [])

    async def create_draft_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        url = f"{self.BASE_URLS['gmail']}/gmail/v1/users/me/drafts"
        raw_email = self._create_raw_email({"to": to, "subject": subject, "body": body})
        payload = {"raw": raw_email}
        response = await self._request("POST", url, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Failed to create draft email: {response.status_code}")
        return response.json()

    @staticmethod
    def _create_raw_email(email_data: Dict[str, Any]) -> str:
        import base64
        from email.mime.text import MIMEText

        message = MIMEText(email_data["body"])
        message["to"] = email_data["to"]
        message["subject"] = email_data["subject"]
        return base64.urlsafe_b64encode(message.as_bytes()).decode()
