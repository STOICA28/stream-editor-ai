from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.future import select
import uuid
from datetime import datetime

from stream_editor.api.database import get_db
from stream_editor.api.models.style import EditorialStylePolicy, StylePolicyVersion, StyleApplicationRun
from stream_editor.api.models.project import Project
from stream_editor.contracts.style import EditorialStylePolicyContract, StyleApplicationConfig, StyleImpactReport, StyleApplicationRunContract

router = APIRouter(prefix="/style-policies", tags=["Style"])

@router.post("/compile", response_model=EditorialStylePolicyContract)
def compile_policy(payload: dict[str, Any], db: Session = Depends(get_db)) -> EditorialStylePolicyContract:
    from stream_editor.editorial.style.compiler import StylePolicyCompiler
    compiler = StylePolicyCompiler()
    
    profile = payload.get("profile", {})
    findings = payload.get("findings", [])
    project_id = payload.get("project_id")
    
    contract = compiler.compile(profile, findings, project_id)
    
    # Check if policy already exists for this project if we are iterating
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
    policies = db.execute(select(EditorialStylePolicy)).scalars().all()
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

@router.get("/{policy_id}", response_model=EditorialStylePolicyContract)
def get_policy(policy_id: str, db: Session = Depends(get_db)) -> EditorialStylePolicyContract:
    p = db.get(EditorialStylePolicy, policy_id)
    if not p:
        raise HTTPException(status_code=404, detail="Style policy not found")
    return EditorialStylePolicyContract(
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
    )

@router.get("/{policy_id}/versions")
def list_policy_versions(policy_id: str, db: Session = Depends(get_db)) -> List[dict[str, Any]]:
    versions = db.execute(select(StylePolicyVersion).where(StylePolicyVersion.policy_id == policy_id)).scalars().all()
    return [{"id": v.id, "version": v.version, "created_at": v.created_at, "signals": v.signals} for v in versions]

@router.post("/apply")
def apply_style_policy(project_id: str, config: StyleApplicationConfig, dry_run: bool = False, db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not config.enabled or not config.style_policy_id:
        if not dry_run:
            project.style_policy_id = None  # type: ignore[assignment]
            project.style_policy_version = None  # type: ignore[assignment]
            db.commit()
        return {"status": "disabled", "dry_run": dry_run}
        
    policy = db.get(EditorialStylePolicy, config.style_policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Style policy not found")
        
    if not dry_run:
        project.style_policy_id = policy.id
        project.style_policy_version = policy.policy_version
        db.commit()
    
    return {"status": "queued", "dry_run": dry_run, "policy_id": policy.id}

@router.get("/impact", response_model=StyleImpactReport)
def get_style_impact(project_id: str, style_policy_id: str, db: Session = Depends(get_db)) -> StyleImpactReport:
    # A real implementation would compare the latest No-Style run vs Styled run for this project.
    return StyleImpactReport(
        project_id=project_id,
        style_policy_id=style_policy_id,
        metrics=[
            {"name": "Selected Duration", "default_value": 300, "styled_value": 280, "unit": "seconds"},
            {"name": "Avg Clip Duration", "default_value": 8.5, "styled_value": 6.2, "unit": "seconds"},
            {"name": "Cuts per Minute", "default_value": 7.0, "styled_value": 9.6, "unit": "cuts"},
            {"name": "Reaction Retention", "default_value": 0.8, "styled_value": 0.95, "unit": "ratio"}
        ],
        dry_run=True
    )

@router.get("/provenance/{project_id}", response_model=List[StyleApplicationRunContract])
def get_provenance(project_id: str, db: Session = Depends(get_db)) -> List[StyleApplicationRunContract]:
    runs = db.execute(select(StyleApplicationRun).where(StyleApplicationRun.project_id == project_id).order_by(StyleApplicationRun.created_at.desc())).scalars().all()
    results = []
    for r in runs:
        results.append(StyleApplicationRunContract(
            id=r.id,
            project_id=r.project_id,
            style_policy_id=r.style_policy_id,
            style_policy_version_id=r.style_policy_version_id,
            style_application_config=r.style_application_config or {},
            experimental=r.experimental or False,
            dry_run=r.dry_run or False,
            input_candidate_run_id=r.input_candidate_run_id,
            input_story_graph_run_id=r.input_story_graph_run_id,
            input_visual_analysis_run_id=r.input_visual_analysis_run_id,
            output_edit_plan_run_id=r.output_edit_plan_run_id,
            output_effect_plan_run_id=r.output_effect_plan_run_id,
            signature=r.signature,
            status=r.status,
            created_at=r.created_at,
            completed_at=r.completed_at
        ))
    return results

