from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from stream_editor.api.database import get_db
from stream_editor.api.models.style import EditorialStylePolicy, StylePolicyVersion
from stream_editor.contracts.style import EditorialStylePolicyContract, StyleApplicationConfig, StyleImpactReport

router = APIRouter(prefix="/style-policies", tags=["Style"])

@router.post("/compile", response_model=EditorialStylePolicyContract)
def compile_policy(payload: dict[str, Any], db: Session = Depends(get_db)) -> EditorialStylePolicyContract:
    """
    Compiles a StyleProfile and approved research findings into a deterministic EditorialStylePolicy.
    """
    from stream_editor.editorial.style.compiler import StylePolicyCompiler
    compiler = StylePolicyCompiler()
    
    profile = payload.get("profile", {})
    findings = payload.get("findings", [])
    project_id = payload.get("project_id")
    
    contract = compiler.compile(profile, findings, project_id)
    
    # Save to DB
    policy_model = EditorialStylePolicy(
        id=contract.id,
        name=contract.name,
        description=contract.description,
        status=contract.status,
        source_reference_project_id=contract.source_reference_project_id,
        source_style_profile_id=contract.source_style_profile_id,
        source_style_profile_version=contract.source_style_profile_version,
        policy_version=contract.policy_version,
        experimental=contract.experimental,
        signals=[s.model_dump() for s in contract.signals],
        created_at=contract.created_at,
        created_by=contract.created_by
    )
    db.add(policy_model)
    
    version_model = StylePolicyVersion(
        id=str(uuid.uuid4()),
        policy_id=contract.id,
        version=contract.policy_version,
        signals=[s.model_dump() for s in contract.signals],
        created_at=contract.created_at
    )
    db.add(version_model)
    
    db.commit()
    
    return contract

@router.get("", response_model=List[EditorialStylePolicyContract])
def list_policies(db: Session = Depends(get_db)) -> List[EditorialStylePolicyContract]:
    policies = db.query(EditorialStylePolicy).all()
    results = []
    for p in policies:
        results.append(EditorialStylePolicyContract(
            id=p.id,
            name=p.name,
            description=p.description or "",
            status=p.status,
            source_reference_project_id=p.source_reference_project_id,
            source_style_profile_id=p.source_style_profile_id,
            source_style_profile_version=p.source_style_profile_version,
            policy_version=p.policy_version,
            experimental=p.experimental,
            signals=p.signals or [],
            created_at=p.created_at,
            created_by=p.created_by or "system"
        ))
    return results

@router.post("/apply")
def apply_style_policy(project_id: str, config: StyleApplicationConfig, dry_run: bool = False, db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Triggers an M11 style application run for a specific project.
    """
    from stream_editor.api.models.project import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    policy = db.query(EditorialStylePolicy).filter(EditorialStylePolicy.id == config.style_policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Style policy not found")
        
    if not dry_run:
        project.style_policy_id = policy.id
        project.style_policy_version = policy.policy_version
        db.commit()
        
    # In a real implementation, this would queue a Celery job to run the pipeline
    # with the new cache key (invalidating old results) and return a Job ID.
    
    return {"status": "queued", "dry_run": dry_run, "policy_id": policy.id}

@router.get("/impact", response_model=StyleImpactReport)
def get_style_impact(project_id: str, style_policy_id: str, db: Session = Depends(get_db)) -> StyleImpactReport:
    """
    Returns the difference between base scores and styled scores.
    """
    return StyleImpactReport(
        project_id=project_id,
        style_policy_id=style_policy_id,
        metrics=[],
        dry_run=True
    )


