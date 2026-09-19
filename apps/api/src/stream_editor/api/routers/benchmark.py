from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.future import select
import uuid
from datetime import datetime, UTC

from stream_editor.api.database import get_db
from stream_editor.api.models.benchmark import (
    EditorialBenchmarkCaseModel,
    EditorialBenchmarkRunModel,
    EditorialBenchmarkResultModel,
    EditorialFailureModel,
    EditorialExperimentModel,
)
from stream_editor.contracts.benchmark import (
    EditorialBenchmarkCase,
    EditorialBenchmarkRun,
    EditorialBenchmarkResult,
    EditorialFailure,
    EditorialExperiment,
    DatasetSplit,
    ExperimentStatus,
)

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])


@router.post("/cases", response_model=EditorialBenchmarkCase)
def create_case(payload: dict[str, Any], db: Session = Depends(get_db)) -> EditorialBenchmarkCase:
    case_id = payload.get("id") or str(uuid.uuid4())
    case_model = EditorialBenchmarkCaseModel(
        id=case_id,
        name=payload["name"],
        source_asset_id=payload["source_asset_id"],
        human_edit_asset_id=payload["human_edit_asset_id"],
        reference_project_id=payload.get("reference_project_id"),
        editor_label=payload.get("editor_label", "human_reference"),
        style_policy_id=payload.get("style_policy_id"),
        duration_source=float(payload["duration_source"]),
        duration_human_edit=float(payload["duration_human_edit"]),
        authorization_status=payload.get("authorization_status", "authorized"),
        split=str(payload.get("split", "TEST")),
        tags=payload.get("tags", []),
        notes=payload.get("notes"),
        created_at=datetime.now(UTC),
    )
    db.add(case_model)
    db.commit()
    db.refresh(case_model)

    return EditorialBenchmarkCase(
        id=case_model.id,
        name=case_model.name,
        source_asset_id=case_model.source_asset_id,
        human_edit_asset_id=case_model.human_edit_asset_id,
        reference_project_id=case_model.reference_project_id,
        editor_label=case_model.editor_label,
        style_policy_id=case_model.style_policy_id,
        duration_source=case_model.duration_source,
        duration_human_edit=case_model.duration_human_edit,
        authorization_status=case_model.authorization_status,
        split=DatasetSplit(case_model.split),
        tags=case_model.tags or [],
        notes=case_model.notes,
        created_at=case_model.created_at,
    )


@router.get("/cases", response_model=List[EditorialBenchmarkCase])
def list_cases(
    split: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[EditorialBenchmarkCase]:
    query = select(EditorialBenchmarkCaseModel)
    if split:
        query = query.where(EditorialBenchmarkCaseModel.split == split)
    models = db.execute(query).scalars().all()
    results = []
    for m in models:
        results.append(
            EditorialBenchmarkCase(
                id=m.id,
                name=m.name,
                source_asset_id=m.source_asset_id,
                human_edit_asset_id=m.human_edit_asset_id,
                reference_project_id=m.reference_project_id,
                editor_label=m.editor_label,
                style_policy_id=m.style_policy_id,
                duration_source=m.duration_source,
                duration_human_edit=m.duration_human_edit,
                authorization_status=m.authorization_status,
                split=DatasetSplit(m.split),
                tags=m.tags or [],
                notes=m.notes,
                created_at=m.created_at,
            )
        )
    return results


@router.get("/cases/{case_id}", response_model=EditorialBenchmarkCase)
def get_case(case_id: str, db: Session = Depends(get_db)) -> EditorialBenchmarkCase:
    m = db.get(EditorialBenchmarkCaseModel, case_id)
    if not m:
        raise HTTPException(status_code=404, detail="Benchmark case not found")
    return EditorialBenchmarkCase(
        id=m.id,
        name=m.name,
        source_asset_id=m.source_asset_id,
        human_edit_asset_id=m.human_edit_asset_id,
        reference_project_id=m.reference_project_id,
        editor_label=m.editor_label,
        style_policy_id=m.style_policy_id,
        duration_source=m.duration_source,
        duration_human_edit=m.duration_human_edit,
        authorization_status=m.authorization_status,
        split=DatasetSplit(m.split),
        tags=m.tags or [],
        notes=m.notes,
        created_at=m.created_at,
    )


@router.post("/runs", response_model=dict[str, Any])
def record_run(payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    run_id = payload.get("id") or str(uuid.uuid4())
    run_model = EditorialBenchmarkRunModel(
        id=run_id,
        benchmark_case_id=payload["benchmark_case_id"],
        project_id=payload["project_id"],
        streameditor_version=payload.get("streameditor_version", "0.1.0"),
        build_commit=payload.get("build_commit", "HEAD"),
        policy_version=payload.get("policy_version", "v1"),
        prompt_versions=payload.get("prompt_versions", {}),
        provider_versions=payload.get("provider_versions", {}),
        style_policy_id=payload.get("style_policy_id"),
        configuration=payload.get("configuration", {}),
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC) if payload.get("completed", False) else None,
        status=payload.get("status", "completed"),
        is_baseline=payload.get("is_baseline", False),
    )
    db.add(run_model)

    # If result included in payload
    if "result" in payload:
        res_data = payload["result"]
        res_model = EditorialBenchmarkResultModel(
            id=str(uuid.uuid4()),
            run_id=run_id,
            case_id=payload["benchmark_case_id"],
            split=res_data.get("split", "TEST"),
            overlap_at_05s=res_data.get("overlap_at_05s", {}),
            overlap_at_10s=res_data.get("overlap_at_10s", {}),
            overlap_at_20s=res_data.get("overlap_at_20s", {}),
            context_metrics=res_data.get("context_metrics", {}),
            narrative_metrics=res_data.get("narrative_metrics", {}),
            pacing_metrics=res_data.get("pacing_metrics", {}),
            effect_metrics=res_data.get("effect_metrics", {}),
            matched_segments_count=int(res_data.get("matched_segments_count", 0)),
            missed_segments_count=int(res_data.get("missed_segments_count", 0)),
            ai_only_segments_count=int(res_data.get("ai_only_segments_count", 0)),
            valid_alternatives_count=int(res_data.get("valid_alternatives_count", 0)),
            root_cause_distribution=res_data.get("root_cause_distribution", {}),
            editor_model=res_data.get("editor_model", "gemini-3.1-pro-high"),
            evaluator_model=res_data.get("evaluator_model", "gemini-3.1-pro-high"),
            model_parity_flag=res_data.get("model_parity_flag", True),
            manual_audit_verified=res_data.get("manual_audit_verified", False),
            created_at=datetime.now(UTC),
        )
        db.add(res_model)

    # If failures included
    for f in payload.get("failures", []):
        f_model = EditorialFailureModel(
            id=str(uuid.uuid4()),
            benchmark_run_id=run_id,
            case_id=payload["benchmark_case_id"],
            failure_type=f["failure_type"],
            root_cause_stage=f["root_cause_stage"],
            source_start=float(f["source_start"]),
            source_end=float(f["source_end"]),
            description=f["description"],
            evidence_trace=f.get("evidence_trace", {}),
            confidence=float(f.get("confidence", 1.0)),
            created_at=datetime.now(UTC),
        )
        db.add(f_model)

    db.commit()
    return {"run_id": run_id, "status": "recorded"}


@router.get("/runs", response_model=List[dict[str, Any]])
def list_runs(
    case_id: Optional[str] = Query(None),
    is_baseline: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
) -> List[dict[str, Any]]:
    query = select(EditorialBenchmarkRunModel)
    if case_id:
        query = query.where(EditorialBenchmarkRunModel.benchmark_case_id == case_id)
    if is_baseline is not None:
        query = query.where(EditorialBenchmarkRunModel.is_baseline == is_baseline)
    models = db.execute(query).scalars().all()
    results = []
    for r in models:
        results.append({
            "id": r.id,
            "benchmark_case_id": r.benchmark_case_id,
            "project_id": r.project_id,
            "streameditor_version": r.streameditor_version,
            "build_commit": r.build_commit,
            "policy_version": r.policy_version,
            "is_baseline": r.is_baseline,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        })
    return results


@router.get("/runs/{run_id}", response_model=dict[str, Any])
def get_run(run_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    run = db.get(EditorialBenchmarkRunModel, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Benchmark run not found")

    result = db.execute(
        select(EditorialBenchmarkResultModel).where(EditorialBenchmarkResultModel.run_id == run_id)
    ).scalar_one_or_none()

    failures = db.execute(
        select(EditorialFailureModel).where(EditorialFailureModel.benchmark_run_id == run_id)
    ).scalars().all()

    return {
        "run": {
            "id": run.id,
            "benchmark_case_id": run.benchmark_case_id,
            "project_id": run.project_id,
            "streameditor_version": run.streameditor_version,
            "build_commit": run.build_commit,
            "is_baseline": run.is_baseline,
            "status": run.status,
            "configuration": run.configuration,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        },
        "result": {
            "overlap_at_05s": result.overlap_at_05s if result else None,
            "overlap_at_10s": result.overlap_at_10s if result else None,
            "overlap_at_20s": result.overlap_at_20s if result else None,
            "context_metrics": result.context_metrics if result else None,
            "narrative_metrics": result.narrative_metrics if result else None,
            "pacing_metrics": result.pacing_metrics if result else None,
            "effect_metrics": result.effect_metrics if result else None,
            "matched_segments_count": result.matched_segments_count if result else 0,
            "missed_segments_count": result.missed_segments_count if result else 0,
            "ai_only_segments_count": result.ai_only_segments_count if result else 0,
            "valid_alternatives_count": result.valid_alternatives_count if result else 0,
            "root_cause_distribution": result.root_cause_distribution if result else {},
        } if result else None,
        "failures": [
            {
                "id": f.id,
                "failure_type": f.failure_type,
                "root_cause_stage": f.root_cause_stage,
                "source_start": f.source_start,
                "source_end": f.source_end,
                "description": f.description,
                "evidence_trace": f.evidence_trace,
                "confidence": f.confidence,
            }
            for f in failures
        ],
    }


@router.post("/experiments", response_model=EditorialExperiment)
def create_experiment(payload: dict[str, Any], db: Session = Depends(get_db)) -> EditorialExperiment:
    exp_id = str(uuid.uuid4())
    exp_model = EditorialExperimentModel(
        id=exp_id,
        name=payload["name"],
        hypothesis=payload["hypothesis"],
        baseline_run_id=payload["baseline_run_id"],
        target_stage=payload["target_stage"],
        proposed_change=payload["proposed_change"],
        status="PROPOSED",
        results_comparison=payload.get("results_comparison"),
        created_at=datetime.now(UTC),
    )
    db.add(exp_model)
    db.commit()
    db.refresh(exp_model)

    return EditorialExperiment(
        id=exp_model.id,
        name=exp_model.name,
        hypothesis=exp_model.hypothesis,
        baseline_run_id=exp_model.baseline_run_id,
        target_stage=payload["target_stage"],
        proposed_change=exp_model.proposed_change,
        status=ExperimentStatus(exp_model.status),
        results_comparison=exp_model.results_comparison,
        created_at=exp_model.created_at,
    )


@router.get("/experiments", response_model=List[EditorialExperiment])
def list_experiments(db: Session = Depends(get_db)) -> List[EditorialExperiment]:
    models = db.execute(select(EditorialExperimentModel)).scalars().all()
    results = []
    for m in models:
        results.append(
            EditorialExperiment(
                id=m.id,
                name=m.name,
                hypothesis=m.hypothesis,
                baseline_run_id=m.baseline_run_id,
                target_stage=m.target_stage,
                proposed_change=m.proposed_change,
                status=ExperimentStatus(m.status),
                results_comparison=m.results_comparison,
                created_at=m.created_at,
                completed_at=m.completed_at,
            )
        )
    return results
