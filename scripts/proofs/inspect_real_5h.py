from sqlalchemy import create_engine, text
import json

e = create_engine('sqlite:///test.db')
conn = e.connect()
pid = 'real-5h-65655576'

print('=== M1 MEDIA ASSETS ===')
for row in conn.execute(text(f'SELECT id, name, path, media_type, file_size_bytes, media_info FROM media_assets WHERE project_id=\"{pid}\"')).fetchall():
    print(f"ID: {row[0]}, name: {row[1]}, path: {row[2]}, type: {row[3]}, size: {row[4]}, info: {row[5]}")

print('\n=== M2 UNDERSTANDING ===')
for row in conn.execute(text(f'SELECT id, provider, status FROM transcript_runs WHERE project_id=\"{pid}\"')).fetchall():
    print(f"TranscriptRun ID: {row[0]}, provider: {row[1]}, status: {row[2]}")
print('Scenes count:', conn.execute(text(f'SELECT count(*) FROM scenes WHERE project_id=\"{pid}\"')).scalar())
print('Audio Events count:', conn.execute(text(f'SELECT count(*) FROM audio_events WHERE project_id=\"{pid}\"')).scalar())
print('Timeline Events count:', conn.execute(text(f'SELECT count(*) FROM timeline_events WHERE project_id=\"{pid}\"')).scalar())
print('Transcript segments count:', conn.execute(text(f'SELECT count(*) FROM transcript_segments WHERE transcript_run_id IN (SELECT id FROM transcript_runs WHERE project_id=\"{pid}\")')).scalar())

print('\n=== M3 CANDIDATE RUNS ===')
for row in conn.execute(text(f'SELECT id, provider, status, derivation_signature FROM candidate_runs WHERE project_id=\"{pid}\"')).fetchall():
    print(f"CandidateRun ID: {row[0]}, provider: {row[1]}, status: {row[2]}, signature: {row[3]}")
print('Candidate segments count:', conn.execute(text(f'SELECT count(*) FROM candidate_segments WHERE run_id IN (SELECT id FROM candidate_runs WHERE project_id=\"{pid}\")')).scalar())

print('\n=== M4 STORY GRAPH RUNS ===')
for row in conn.execute(text(f'SELECT id, provider, status, derivation_signature FROM story_graph_runs WHERE project_id=\"{pid}\"')).fetchall():
    print(f"StoryGraphRun ID: {row[0]}, provider: {row[1]}, status: {row[2]}, signature: {row[3]}")
print('Story nodes count:', conn.execute(text(f'SELECT count(*) FROM story_nodes WHERE story_graph_run_id IN (SELECT id FROM story_graph_runs WHERE project_id=\"{pid}\")')).scalar())
print('Story edges count:', conn.execute(text(f'SELECT count(*) FROM story_edges WHERE story_graph_run_id IN (SELECT id FROM story_graph_runs WHERE project_id=\"{pid}\")')).scalar())
print('Narrative threads count:', conn.execute(text(f'SELECT count(*) FROM narrative_threads WHERE story_graph_run_id IN (SELECT id FROM story_graph_runs WHERE project_id=\"{pid}\")')).scalar())

print('\n=== M5 EDIT PLAN RUNS ===')
for row in conn.execute(text(f'SELECT id, provider, status, derivation_signature FROM edit_plan_runs WHERE project_id=\"{pid}\"')).fetchall():
    print(f"EditPlanRun ID: {row[0]}, provider: {row[1]}, status: {row[2]}, signature: {row[3]}")
for row in conn.execute(text(f'SELECT id, run_id, version, status, selected_duration, original_duration, clip_count FROM edit_plans WHERE project_id=\"{pid}\"')).fetchall():
    print(f"EditPlan ID: {row[0]}, run_id: {row[1]}, v{row[2]}, status: {row[3]}, selected: {row[4]}s, orig: {row[5]}s, clips: {row[6]}")

print('\n=== M7 VISUAL ANALYSIS RUNS ===')
for row in conn.execute(text(f'SELECT id, provider, status, derivation_signature FROM visual_analysis_runs WHERE project_id=\"{pid}\"')).fetchall():
    print(f"VisualAnalysisRun ID: {row[0]}, provider: {row[1]}, status: {row[2]}, signature: {row[3]}")

print('\n=== M8 EFFECT PLAN RUNS ===')
for row in conn.execute(text(f'SELECT id, provider, status, derivation_signature FROM effect_plan_runs WHERE project_id=\"{pid}\"')).fetchall():
    print(f"EffectPlanRun ID: {row[0]}, provider: {row[1]}, status: {row[2]}, signature: {row[3]}")
print('Effect instructions count:', conn.execute(text(f'SELECT count(*) FROM effect_instructions WHERE effect_plan_run_id IN (SELECT id FROM effect_plan_runs WHERE project_id=\"{pid}\")')).scalar())

print('\n=== M9 RENDER JOBS ===')
for row in conn.execute(text(f'SELECT id, status, edit_plan_id, effect_plan_run_id, output_asset_id FROM render_jobs WHERE project_id=\"{pid}\"')).fetchall():
    print(f"RenderJob ID: {row[0]}, status: {row[1]}, plan: {row[2]}, effect: {row[3]}, output: {row[4]}")
