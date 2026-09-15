import uuid
from stream_editor.contracts.edit_plan import EditPlanConfig
from stream_editor.contracts.editorial import StoryGraphContract, CandidateSegmentContract
from stream_editor.editorial.planning.mock import MockGlobalEditorialPlanner


def test_mock_planner() -> None:
    planner = MockGlobalEditorialPlanner()
    candidates = [
        CandidateSegmentContract(
            id=str(uuid.uuid4()), project_id="test", core_start=0.0, core_end=10.0,
            start_time=0.0, end_time=10.0,
            score_importance=0.9
        ),
        CandidateSegmentContract(
            id=str(uuid.uuid4()), project_id="test", core_start=10.0, core_end=20.0,
            start_time=10.0, end_time=20.0,
            score_importance=0.8
        )
    ]
    graph = StoryGraphContract(id=str(uuid.uuid4()), project_id="test", run_id=str(uuid.uuid4()), version=1, status="completed")
    config = EditPlanConfig(target_duration_seconds=10.0, tolerance_seconds=0.0)
    
    plan = planner.generate_plan(
        project_id="test",
        run_id=str(uuid.uuid4()),
        graph=graph,
        candidates=candidates,
        config=config
    )
    
    assert len(plan.clips) == 1
    assert plan.clips[0].candidate_id == candidates[0].id
