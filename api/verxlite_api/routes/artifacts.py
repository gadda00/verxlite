"""
Artifacts Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import Optional, List
from datetime import datetime

from verxlite_api.db.session import get_db
from verxlite_api.models.user import User
from verxlite_api.models.artifact import Artifact
from verxlite_api.models.workflow_run import WorkflowRun
from verxlite_api.schemas.artifact import ArtifactResponse, ArtifactListResponse
from verxlite_api.utils.logger import get_logger
from verxlite_api.deps import get_current_user

router = APIRouter(tags=["artifacts"])
logger = get_logger("artifacts")


@router.get("/", response_model=ArtifactListResponse)
async def list_artifacts(
    request: Request,
    run_id: Optional[str] = None,
    artifact_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List artifacts with optional filters (scoped to current tenant)."""
    query = (
        db.query(Artifact)
        .join(WorkflowRun)
        .filter(WorkflowRun.tenant_id == current_user.tenant_id)
    )

    if run_id:
        query = query.filter(Artifact.run_id == run_id)
    if artifact_type:
        query = query.filter(Artifact.artifact_type == artifact_type)

    total = query.count()
    artifacts = (
        query.order_by(Artifact.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return ArtifactListResponse(
        artifacts=[ArtifactResponse.model_validate(a) for a in artifacts],
        total=total,
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    request: Request,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of an artifact (scoped to current tenant)."""
    artifact = (
        db.query(Artifact)
        .join(WorkflowRun)
        .filter(
            Artifact.id == artifact_id,
            WorkflowRun.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )
    return ArtifactResponse.model_validate(artifact)
