"""Unit tests for Benchmark API router."""

import pytest
from fastapi.testclient import TestClient
import uuid

from stream_editor.api.main import app
from stream_editor.api.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from stream_editor.api.models.project import Project, MediaAsset

# Test database
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_benchmark_api.db"
test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    
    # Create prerequisite project and media assets
    db = TestingSessionLocal()
    proj = Project(id="proj-bm-1", name="Benchmark Project")
    db.add(proj)
    src_asset = MediaAsset(id="asset-src-1", project_id="proj-bm-1", name="src", path="test_src.mp4", media_type="video")
    edit_asset = MediaAsset(id="asset-edit-1", project_id="proj-bm-1", name="edit", path="test_edit.mp4", media_type="video")
    db.add(src_asset)
    db.add(edit_asset)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    import os
    if os.path.exists("./test_benchmark_api.db"):
        try:
            os.remove("./test_benchmark_api.db")
        except PermissionError:
            pass


def test_benchmark_case_and_run_lifecycle():
    client = TestClient(app)

    # 1. Create Benchmark Case
    case_payload = {
        "id": "case-test-1",
        "name": "Held-Out Test 1",
        "source_asset_id": "asset-src-1",
        "human_edit_asset_id": "asset-edit-1",
        "reference_project_id": "proj-bm-1",
        "duration_source": 120.0,
        "duration_human_edit": 45.0,
        "split": "TEST",
        "tags": ["gaming", "unseen"],
    }
    resp = client.post("/api/v1/benchmarks/cases", json=case_payload)
    assert resp.status_code == 200
    case_data = resp.json()
    assert case_data["id"] == "case-test-1"
    assert case_data["split"] == "TEST"

    # 2. List Cases
    resp = client.get("/api/v1/benchmarks/cases?split=TEST")
    assert resp.status_code == 200
    cases = resp.json()
    assert len(cases) >= 1
    assert cases[0]["id"] == "case-test-1"

    # 3. Get Case by ID
    resp = client.get("/api/v1/benchmarks/cases/case-test-1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Held-Out Test 1"

    # 4. Record Benchmark Run
    run_payload = {
        "id": "run-bm-1",
        "benchmark_case_id": "case-test-1",
        "project_id": "proj-bm-1",
        "streameditor_version": "0.1.0",
        "build_commit": "HEAD",
        "is_baseline": True,
        "status": "completed",
        "result": {
            "split": "TEST",
            "overlap_at_05s": {"precision": 0.8, "recall": 0.75, "f1": 0.77},
            "overlap_at_10s": {"precision": 0.85, "recall": 0.82, "f1": 0.83},
            "overlap_at_20s": {"precision": 0.9, "recall": 0.88, "f1": 0.89},
            "context_metrics": {"good_context_match_count": 5},
            "narrative_metrics": {"setup_payoff_completeness": 0.8},
            "pacing_metrics": {"cuts_per_minute": 4.2},
            "effect_metrics": {"effect_agreement_rate": 0.7},
            "matched_segments_count": 5,
            "missed_segments_count": 1,
            "ai_only_segments_count": 1,
            "valid_alternatives_count": 1,
            "root_cause_distribution": {"M5:BUDGET_EXCLUSION": 1},
        },
        "failures": [
            {
                "failure_type": "BUDGET_EXCLUSION",
                "root_cause_stage": "M5",
                "source_start": 30.0,
                "source_end": 40.0,
                "description": "Dropped during knapsack optimization",
                "confidence": 1.0,
            }
        ],
    }
    resp = client.post("/api/v1/benchmarks/runs", json=run_payload)
    assert resp.status_code == 200
    assert resp.json()["run_id"] == "run-bm-1"

    # 5. List Runs
    resp = client.get("/api/v1/benchmarks/runs?is_baseline=true")
    assert resp.status_code == 200
    runs = resp.json()
    assert len(runs) >= 1
    assert runs[0]["id"] == "run-bm-1"
    assert runs[0]["is_baseline"] is True

    # 6. Get Run Details
    resp = client.get("/api/v1/benchmarks/runs/run-bm-1")
    assert resp.status_code == 200
    run_detail = resp.json()
    assert run_detail["run"]["id"] == "run-bm-1"
    assert run_detail["result"]["matched_segments_count"] == 5
    assert len(run_detail["failures"]) == 1

    # 7. Create and List Experiments
    exp_payload = {
        "name": "Exp-001 Lower Candidate Threshold",
        "hypothesis": "Lowering threshold from 0.7 to 0.5 will improve recall on subtle humor",
        "baseline_run_id": "run-bm-1",
        "target_stage": "M3",
        "proposed_change": "M3 candidate score threshold = 0.5",
    }
    resp = client.post("/api/v1/benchmarks/experiments", json=exp_payload)
    assert resp.status_code == 200
    exp = resp.json()
    assert exp["status"] == "PROPOSED"
    assert exp["target_stage"] == "M3"

    resp = client.get("/api/v1/benchmarks/experiments")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
