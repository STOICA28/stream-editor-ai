import ast
from pathlib import Path

def test_m2_does_not_import_m7_models():
    """
    Ensure that Stage M2 (Understanding) does not import or query Stage M7
    (visual_analysis/visual_event/focus_target) models.
    """
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    analysis_dir = root_dir / "packages" / "analysis" / "src" / "stream_editor" / "analysis"
    worker_tasks_dir = root_dir / "apps" / "worker" / "src" / "stream_editor" / "worker" / "tasks"
    
    forbidden_imports = [
        "DBVisualEvent",
        "VisualAnalysisRun",
        "FocusTarget",
        "FocusTargetSchema",
    ]
    
    violations = []

    # 1. Check M2 analysis modules (excluding providers/visual which is M7)
    for p in analysis_dir.glob("*.py"):
        _check_file(p, forbidden_imports, violations)
    for p in (analysis_dir / "providers").glob("*.py"):
        _check_file(p, forbidden_imports, violations)

    # 2. Check M2 tasks in apps/worker/src/stream_editor/worker/tasks/pipeline.py
    pipeline_file = worker_tasks_dir / "pipeline.py"
    if pipeline_file.exists():
        with open(pipeline_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        m2_task_names = {
            "analyze_visual_observations_task",
            "normalize_timeline_task",
            "transcribe_task",
            "detect_scenes_task",
            "analyze_audio_task",
            "extract_audio_task",
        }
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in m2_task_names:
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Import):
                        for name in subnode.names:
                            for forbidden in forbidden_imports:
                                if forbidden in name.name:
                                    violations.append(f"M2 task {node.name}: imports {name.name}")
                    elif isinstance(subnode, ast.ImportFrom):
                        if subnode.module:
                            for forbidden in forbidden_imports:
                                if forbidden in subnode.module:
                                    violations.append(f"M2 task {node.name}: imports from {subnode.module}")
                        for name in subnode.names:
                            for forbidden in forbidden_imports:
                                if forbidden in name.name:
                                    violations.append(f"M2 task {node.name}: imports {name.name}")

    violations = list(set(violations))
    assert not violations, f"Architectural violation: M2 code imports M7 models: {violations}"


def _check_file(filepath: Path, forbidden_imports: list[str], violations: list[str]) -> None:
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                for forbidden in forbidden_imports:
                    if forbidden in name.name:
                        violations.append(f"{filepath.name}: imports {name.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for forbidden in forbidden_imports:
                    if forbidden in node.module:
                        violations.append(f"{filepath.name}: imports from {node.module}")
            for name in node.names:
                for forbidden in forbidden_imports:
                    if forbidden in name.name:
                        violations.append(f"{filepath.name}: imports {name.name}")
