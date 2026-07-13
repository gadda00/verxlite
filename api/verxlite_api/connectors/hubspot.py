"""
HubSpot Connector
"""

from typing import Dict, Any, Optional, List
import httpx
import json
from datetime import datetime, timedelta

from verxlite_api.config import settings
from verxlite_api.db.session import session
from verxlite_api.models.connection import Connection
from verxlite_api.utils.logger import get_logger
from verxlite_api.utils.encryption import decrypt_data, encrypt_data

logger = get_logger("hubspot_connector")


class HubSpotConnector:
    """
    Connector for HubSpot CRM.
    """
    
    BASE_URL = "https://api.hubapi.com"
    
    def __init__(self, connection_id: str):
        self.db = session()
        self.connection = self._get_connection(connection_id)
        self.access_token = self._get_access_token()
    
    def _get_connection(self, connection_id: str) -> Connection:
        """Get the HubSpot connection from the database."""
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id,
            Connection.provider == "hubspot",
        ).first()
        
        if not connection:
            raise ValueError(f"HubSpot connection not found: {connection_id}")
        
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
            "grant_type": "refresh_token",
            "client_id": settings.HUBSPOT_CLIENT_ID,
            "client_secret": settings.HUBSPOT_CLIENT_SECRET,
            "refresh_token": refresh_token,
        }
        
        async with httpx.AsyncClient() as client:
            response = client.post(
                f"{self.BASE_URL}/oauth/v1/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
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
        """Get headers for HubSpot API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
    
    async def get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a contact by email address.
        """
        url = f"{self.BASE_URL}/crm/v3/objects/contacts"
        params = {
            "q": email,
            "properties": ["email", "firstname", "lastname", "company"],
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
                if response.status_code == 404:
                    return None
                raise ValueError(f"Failed to get contact: {response.status_code}")
            
            results = response.json().get("results", [])
            return results[0] if results else None
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Get a contact by ID.
        """
        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                self.access_token = self._refresh_access_token()
                response = await client.get(url, headers=self._get_headers())
            
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
        """
        Create a new contact.
        """
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
            
            if response.status_code != 201:
                raise ValueError(f"Failed to create contact: {response.status_code}")
            
            return response.json()
    
    async def update_contact(
        self,
        contact_id: str,
        **properties,
    ) -> Dict[str, Any]:
        """
        Update a contact.
        """
        url = f"{self.BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        
        payload = {
            "properties": properties,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self._get_headers(),
                json=payload,
            )
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                self.access_token = self._refresh_access_token()
                response = await client.patch(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to update contact: {response.status_code}")
            
            return response.json()
    
    async def create_note(
        self,
        contact_id: str,
        body: str,
    ) -> Dict[str, Any]:
        """
        Create a note for a contact.
        """
        url = f"{self.BASE_URL}/crm/v3/objects/notes"
        
        payload = {
            "properties": {
                "hs_note_body": body,
                "hs_associated_object_id": contact_id,
                "hs_associated_object_type": "CONTACT",
            }
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
        """
        Create a task for a contact.
        """
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
            
            if response.status_code != 201:
                raise ValueError(f"Failed to create task: {response.status_code}")
            
            return response.json()
    
    async def update_deal_stage(
        self,
        deal_id: str,
        stage: str,
    ) -> Dict[str, Any]:
        """
        Update a deal's stage.
        """
        url = f"{self.BASE_URL}/crm/v3/objects/deals/{deal_id}"
        
        payload = {
            "properties": {
                "dealstage": stage,
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self._get_headers(),
                json=payload,
            )
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                self.access_token = self._refresh_access_token()
                response = await client.patch(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to update deal stage: {response.status_code}")
            
            return response.json()
