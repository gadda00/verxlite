"""
Artifacts Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.models.artifact import Artifact
from verxlite_api.models.workflow_run import WorkflowRun
from verxlite_api.utils.logger import get_logger

router = APIRouter(prefix="/artifacts", tags=["artifacts"])
logger = get_logger("artifacts")


class ArtifactResponse(BaseModel):
    id: str
    run_id: str
    artifact_type: str
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    content_summary: Optional[str] = None
    created_at: datetime


class ArtifactListResponse(BaseModel):
    artifacts: List[ArtifactResponse]


@router.get("/", response_model=ArtifactListResponse)
async def list_artifacts(
    request: Request,
    run_id: Optional[str] = None,
    artifact_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db=Depends(get_db),
):
    """
    List artifacts with optional filters.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    tenant_id = "test-tenant-id"
    
    query = db.query(Artifact).join(WorkflowRun).filter(WorkflowRun.tenant_id == tenant_id)
    
    if run_id:
        query = query.filter(Artifact.run_id == run_id)
    
    if artifact_type:
        query = query.filter(Artifact.artifact_type == artifact_type)
    
    artifacts = query.order_by(Artifact.created_at.desc()).limit(limit).offset(offset).all()
    
    return ArtifactListResponse(
        artifacts=[
            ArtifactResponse(
                id=artifact.id,
                run_id=artifact.run_id,
                artifact_type=artifact.artifact_type,
                external_id=artifact.external_id,
                external_url=artifact.external_url,
                content_summary=artifact.content_summary,
                created_at=artifact.created_at,
            )
            for artifact in artifacts
        ]
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Get details of an artifact.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    tenant_id = "test-tenant-id"
    
    artifact = db.query(Artifact).join(WorkflowRun).filter(
        Artifact.id == artifact_id,
        WorkflowRun.tenant_id == tenant_id,
    ).first()
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )
    
    return ArtifactResponse(
        id=artifact.id,
        run_id=artifact.run_id,
        artifact_type=artifact.artifact_type,
        external_id=artifact.external_id,
        external_url=artifact.external_url,
        content_summary=artifact.content_summary,
        created_at=artifact.created_at,
    )
