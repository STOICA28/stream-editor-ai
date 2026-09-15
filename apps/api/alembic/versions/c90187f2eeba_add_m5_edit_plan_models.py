"""add_m5_edit_plan_models

Revision ID: c90187f2eeba
Revises: a38b5fbdbe72
Create Date: 2026-09-15 09:54:02.569875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c90187f2eeba'
down_revision: Union[str, None] = 'a38b5fbdbe72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # M5 Edit Plan Models
    
    bind = op.get_bind()
    from sqlalchemy.engine.reflection import Inspector
    inspector = Inspector.from_engine(bind)
    tables = inspector.get_table_names()

    # We must first drop the empty placeholder tables from any previous schema creation
    if 'edit_clips' in tables:
        op.drop_table('edit_clips')
    if 'edit_plans' in tables:
        op.drop_table('edit_plans')
    if 'edit_plan_versions' in tables:
        op.drop_table('edit_plan_versions')
    
    op.create_table(
        'edit_plan_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id')),
        sa.Column('source_asset_id', sa.String(), sa.ForeignKey('media_assets.id')),
        sa.Column('candidate_run_id', sa.String(), sa.ForeignKey('candidate_runs.id'), nullable=True),
        sa.Column('story_graph_run_id', sa.String(), sa.ForeignKey('story_graph_runs.id'), nullable=True),
        
        sa.Column('target_duration_seconds', sa.Float(), nullable=True),
        sa.Column('tolerance_seconds', sa.Float(), nullable=True),
        
        sa.Column('planning_profile', sa.String()),
        sa.Column('provider', sa.String()),
        sa.Column('model', sa.String()),
        sa.Column('prompt_version', sa.String()),
        sa.Column('planner_version', sa.String()),
        
        sa.Column('derivation_signature', sa.String()),
        sa.Column('status', sa.String(), default='running'),
        sa.Column('error_message', sa.String(), nullable=True),
        
        sa.Column('created_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('derivation_signature')
    )

    op.create_table(
        'edit_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id')),
        sa.Column('run_id', sa.String(), sa.ForeignKey('edit_plan_runs.id')),
        sa.Column('version', sa.Integer()),
        sa.Column('status', sa.String()),
        sa.Column('original_duration', sa.Float()),
        sa.Column('selected_duration', sa.Float()),
        sa.Column('compression_ratio', sa.Float()),
        sa.Column('clip_count', sa.Integer()),
        sa.Column('locked', sa.Boolean()),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'edit_clips',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('plan_id', sa.String(), sa.ForeignKey('edit_plans.id')),
        sa.Column('source_start', sa.Float()),
        sa.Column('source_end', sa.Float()),
        sa.Column('core_start', sa.Float(), nullable=True),
        sa.Column('core_end', sa.Float(), nullable=True),
        sa.Column('output_start', sa.Float()),
        sa.Column('output_end', sa.Float()),
        
        sa.Column('candidate_id', sa.String(), sa.ForeignKey('candidate_segments.id'), nullable=True),
        sa.Column('narrative_thread_id', sa.String(), nullable=True),
        sa.Column('story_node_id', sa.String(), sa.ForeignKey('story_nodes.id'), nullable=True),
        
        sa.Column('selection_reason', sa.String()),
        sa.Column('priority', sa.String()),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('locked', sa.Boolean()),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('edit_clips')
    op.drop_table('edit_plans')
    op.drop_table('edit_plan_runs')
