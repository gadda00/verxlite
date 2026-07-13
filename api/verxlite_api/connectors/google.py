"""
Google Connector
"""

from typing import Dict, Any, Optional, List
import httpx
import json
from datetime import datetime, timedelta

from verxlite_api.config import settings
from verxlite_api.db.session import session
from verxlite_api.models.connection import Connection
from verxlite_api.utils.logger import get_logger
from verxlite_api.utils.encryption import decrypt_data

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
    
    def __init__(self, connection_id: str):
        self.db = session()
        self.connection = self._get_connection(connection_id)
        self.access_token = self._get_access_token()
    
    def _get_connection(self, connection_id: str) -> Connection:
        """Get the Google connection from the database."""
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id,
            Connection.provider == "google",
        ).first()
        
        if not connection:
            raise ValueError(f"Google connection not found: {connection_id}")
        
        return connection
    
    def _get_access_token(self) -> str:
        """Get the decrypted access token."""
        if not self.connection.access_token:
            raise ValueError("No access token for this connection")
        
        return decrypt_data(self.connection.access_token, settings.ENCRYPTION_KEY)
    
    def _refresh_access_token(self) -> str:
        """Refresh the access token if expired."""
        if not self.connection.refresh_token:
            raise ValueError("No refresh token for this connection")
        
        refresh_token = decrypt_data(
            self.connection.refresh_token,
            settings.ENCRYPTION_KEY
        )
        
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        
        async with httpx.AsyncClient() as client:
            response = client.post(
                "https://oauth2.googleapis.com/token",
                data=data,
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to refresh access token")
            
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            new_expires_in = token_data.get("expires_in")
            
            # Update connection
            self.connection.access_token = encrypt_data(
                new_access_token,
                settings.ENCRYPTION_KEY
            )
            self.connection.expires_at = datetime.utcnow() + timedelta(
                seconds=new_expires_in - 60
            )
            self.db.commit()
            
            return new_access_token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Google API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
    
    async def get_calendar_event(self, event_id: str) -> Dict[str, Any]:
        """
        Get a calendar event by ID.
        """
        url = f"{self.BASE_URLS['calendar']}/calendars/primary/events/{event_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                self.access_token = self._refresh_access_token()
                response = await client.get(url, headers=self._get_headers())
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get calendar event: {response.status_code}")
            
            return response.json()
    
    async def list_calendar_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List calendar events.
        """
        url = f"{self.BASE_URLS['calendar']}/calendars/primary/events"
        params = {
            "maxResults": max_results,
        }
        
        if time_min:
            params["timeMin"] = time_min.isoformat() + "Z"
        if time_max:
            params["timeMax"] = time_max.isoformat() + "Z"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
            )
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                self.access_token = self._refresh_access_token()
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to list calendar events: {response.status_code}")
            
            return response.json().get("items", [])
    
    async def get_email_thread(self, thread_id: str) -> Dict[str, Any]:
        """
        Get an email thread by ID.
        """
        url = f"{self.BASE_URLS['gmail']}/gmail/v1/users/me/threads/{thread_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                self.access_token = self._refresh_access_token()
                response = await client.get(url, headers=self._get_headers())
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get email thread: {response.status_code}")
            
            return response.json()
    
    async def search_emails(
        self,
        query: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search emails.
        """
        url = f"{self.BASE_URLS['gmail']}/gmail/v1/users/me/messages"
        params = {
            "q": query,
            "maxResults": max_results,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
            )
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                self.access_token = self._refresh_access_token()
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to search emails: {response.status_code}")
            
            return response.json().get("messages", [])
    
    async def create_draft_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """
        Create a draft email.
        """
        url = f"{self.BASE_URLS['gmail']}/gmail/v1/users/me/drafts"
        
        # Create email body
        email_body = {
            "to": to,
            "subject": subject,
            "body": body,
        }
        
        # Create raw email (base64 encoded)
        raw_email = self._create_raw_email(email_body)
        
        payload = {
            "raw": raw_email,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload,
            )
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                self.access_token = self._refresh_access_token()
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to create draft email: {response.status_code}")
            
            return response.json()
    
    def _create_raw_email(self, email_data: Dict[str, Any]) -> str:
        """
        Create a raw email for Gmail API.
        """
        import base64
        from email.mime.text import MIMEText
        
        message = MIMEText(email_data["body"])
        message["to"] = email_data["to"]
        message["subject"] = email_data["subject"]
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return raw_message
