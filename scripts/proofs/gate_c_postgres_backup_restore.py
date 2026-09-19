import subprocess
import os
import json
from datetime import datetime, UTC
from sqlalchemy import create_engine, text

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr

print('=== GATE C: POSTGRESQL BACKUP -> RESTORE PROOF ===')
source_db = 'streameditor'
restore_db = 'streameditor_recovery'
backup_file = 'data/postgres_backup.sql'
os.makedirs('data', exist_ok=True)

# 1. Pre-backup row counts
src_url = 'postgresql://streameditor:streameditor@127.0.0.1:5432/' + source_db
src_engine = create_engine(src_url)
tables = [
    'projects', 'media_assets', 'candidate_runs', 'story_graph_runs',
    'edit_plan_runs', 'edit_plans', 'visual_analysis_runs', 'effect_plan_runs',
    'render_jobs', 'style_application_runs'
]
src_counts = {}
with src_engine.connect() as conn:
    for t in tables:
        src_counts[t] = conn.execute(text(f'SELECT count(*) FROM {t}')).scalar()

print(f'Source DB: {source_db}')
print(f'Source Row Counts: {src_counts}')

# 2. Execute pg_dump
backup_start = datetime.now(UTC).isoformat()
dump_cmd = f'wsl -d kali-linux -u root sh -c "pg_dump -U streameditor -h 127.0.0.1 {source_db} > /tmp/backup.sql"'
rc, out, err = run_cmd(dump_cmd)
if rc != 0:
    print(f'pg_dump failed: {err}')
    exit(1)

# Copy out to verify file size
run_cmd(f'wsl -d kali-linux -u root sh -c "cp /tmp/backup.sql /mnt/c/Users/adria/Documents/EditorDirectos/stream-editor-ai/{backup_file}"')
backup_size = os.path.getsize(backup_file)
print(f'Backup Timestamp: {backup_start}')
print(f'Backup File Size: {backup_size} bytes')
print(f'pg_dump Exit Status: {rc}')

# 3. Create NEW EMPTY recovery database
run_cmd(f'wsl -d kali-linux -u root psql -U postgres -h 127.0.0.1 -c "DROP DATABASE IF EXISTS {restore_db};"')
rc_create, out, err = run_cmd(f'wsl -d kali-linux -u root psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE {restore_db} OWNER streameditor;"')
if rc_create != 0:
    print(f'Create recovery DB failed: {err}')
    exit(1)
print(f'Created clean empty recovery database: {restore_db}')

# 4. Restore into empty recovery database
restore_cmd = f'wsl -d kali-linux -u root sh -c "psql -U streameditor -h 127.0.0.1 -d {restore_db} < /tmp/backup.sql"'
rc_restore, out, err = run_cmd(restore_cmd)
print(f'Restore Exit Status: {rc_restore}')

# 5. Query restored DB and verify row counts & IDs
restore_url = 'postgresql://streameditor:streameditor@127.0.0.1:5432/' + restore_db
restore_engine = create_engine(restore_url)
restore_counts = {}
with restore_engine.connect() as conn:
    for t in tables:
        restore_counts[t] = conn.execute(text(f'SELECT count(*) FROM {t}')).scalar()

print(f'Restored Row Counts: {restore_counts}')
assert src_counts == restore_counts, f'Row count mismatch! {src_counts} != {restore_counts}'
print('LOGICAL EQUALITY VERIFIED: All table row counts match exactly!')

# 6. Verify Representative Original IDs Exist
sample_ids = {
    'Project': ('projects', 'real-5h-65655576'),
    'MediaAsset': ('media_assets', '859fc763-9d32-4590-b7ab-6cf4032e6d7b'),
    'CandidateRun': ('candidate_runs', 'd0a986bf-04b6-4a33-bc1f-fcaac7219079'),
    'StoryGraphRun': ('story_graph_runs', '92df3acd-43dd-45d7-8864-7643fba393c2'),
    'EditPlanRun': ('edit_plan_runs', '3e6a3f93-ae80-4494-a66b-f2e2fcf9759a'),
    'EditPlan (M6)': ('edit_plans', 'bc6aba0a-81c5-4e8c-bc5d-f60dd7e1d1b1'),
    'VisualAnalysisRun': ('visual_analysis_runs', '60c2290c-b453-4542-8310-915d0fdb7149'),
    'EffectPlanRun': ('effect_plan_runs', 'a468cace-69b1-4bc6-b65f-5aaa6073bbbf'),
    'RenderJob': ('render_jobs', 'cd5355af-3b67-49ed-8637-93b1c1c498d4'),
    'StyleApplicationRun': ('style_application_runs', 'rep-style-app-run')
}

with restore_engine.connect() as conn:
    for entity, (table, expected_id) in sample_ids.items():
        found = conn.execute(text(f'SELECT count(*) FROM {table} WHERE id = :id'), {'id': expected_id}).scalar()
        assert found == 1, f'Entity {entity} with ID {expected_id} not found in restored DB!'
        print(f'Verified {entity}: ID {expected_id} exists in restored DB')

# 7. Referential Integrity Check
with restore_engine.connect() as conn:
    query = text('''
        SELECT 
            p.id as project_id,
            m.id as media_asset_id,
            cr.id as candidate_run_id,
            sgr.id as story_graph_run_id,
            epr.id as edit_plan_run_id,
            ep.id as edit_plan_id,
            vr.id as visual_analysis_run_id,
            er.id as effect_plan_run_id,
            rj.id as render_job_id
        FROM projects p
        JOIN media_assets m ON m.project_id = p.id AND m.id = '859fc763-9d32-4590-b7ab-6cf4032e6d7b'
        JOIN candidate_runs cr ON cr.project_id = p.id AND cr.source_asset_id = m.id
        JOIN story_graph_runs sgr ON sgr.project_id = p.id AND sgr.candidate_run_id = cr.id
        JOIN edit_plan_runs epr ON epr.project_id = p.id AND epr.story_graph_run_id = sgr.id
        JOIN edit_plans ep ON ep.project_id = p.id AND ep.id = 'bc6aba0a-81c5-4e8c-bc5d-f60dd7e1d1b1'
        JOIN visual_analysis_runs vr ON vr.project_id = p.id AND vr.source_asset_id = m.id
        JOIN effect_plan_runs er ON er.project_id = p.id AND er.edit_plan_id = ep.id
        JOIN render_jobs rj ON rj.project_id = p.id AND rj.edit_plan_id = ep.id
    ''')
    res = conn.execute(query).fetchone()
    assert res is not None, 'Referential integrity chain failed to resolve in restored DB!'
    print('REFERENTIAL INTEGRITY VERIFIED: Continuous chain resolved completely across all M1->M9 entities!')
    print('Resolved Chain IDs:', res)

print('=== GATE C POSTGRESQL BACKUP -> RESTORE: FULL PASS ===')
