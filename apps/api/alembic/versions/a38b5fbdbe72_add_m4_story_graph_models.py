"""add_m4_story_graph_models

Revision ID: a38b5fbdbe72
Revises: 93d78dd465dc
Create Date: 2026-09-15 09:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a38b5fbdbe72"
down_revision: Union[str, None] = "93d78dd465dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "story_graph_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("source_asset_id", sa.String(), sa.ForeignKey("media_assets.id"), nullable=True),
        sa.Column("candidate_run_id", sa.String(), sa.ForeignKey("candidate_runs.id"), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("flash_model", sa.String(), nullable=True),
        sa.Column("pro_model", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("generator_version", sa.String(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=True),
        sa.Column("derivation_signature", sa.String(), nullable=True, unique=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("node_count", sa.Integer(), nullable=True),
        sa.Column("edge_count", sa.Integer(), nullable=True),
        sa.Column("thread_count", sa.Integer(), nullable=True),
        sa.Column("callback_count", sa.Integer(), nullable=True),
        sa.Column("setup_payoff_pairs", sa.Integer(), nullable=True),
        sa.Column("orphan_node_count", sa.Integer(), nullable=True),
        sa.Column("flash_requests", sa.Integer(), nullable=True),
        sa.Column("pro_requests", sa.Integer(), nullable=True),
        sa.Column("total_input_tokens", sa.Integer(), nullable=True),
        sa.Column("total_output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "story_nodes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_graph_run_id", sa.String(), sa.ForeignKey("story_graph_runs.id"), nullable=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("node_type", sa.String(), nullable=True),
        sa.Column("start_time", sa.Float(), nullable=True),
        sa.Column("end_time", sa.Float(), nullable=True),
        sa.Column("candidate_id", sa.String(), sa.ForeignKey("candidate_segments.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("context_requirement", sa.JSON(), nullable=True),
        sa.Column("graph_narrative_value", sa.Float(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("chapter_index", sa.Integer(), nullable=True),
        sa.Column("node_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "story_edges",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_graph_run_id", sa.String(), sa.ForeignKey("story_graph_runs.id"), nullable=True),
        sa.Column("source_node_id", sa.String(), sa.ForeignKey("story_nodes.id"), nullable=True),
        sa.Column("target_node_id", sa.String(), sa.ForeignKey("story_nodes.id"), nullable=True),
        sa.Column("relation_type", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("dependency_strength", sa.String(), nullable=True),
        sa.Column("dependency_strength_score", sa.Float(), nullable=True),
        sa.Column("evidence_summary", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("validated", sa.Integer(), nullable=True),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "narrative_threads",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_graph_run_id", sa.String(), sa.ForeignKey("story_graph_runs.id"), nullable=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("thread_type", sa.String(), nullable=True),
        sa.Column("first_occurrence_time", sa.Float(), nullable=True),
        sa.Column("last_occurrence_time", sa.Float(), nullable=True),
        sa.Column("is_resolved", sa.Integer(), nullable=True),
        sa.Column("importance", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "node_thread_memberships",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("node_id", sa.String(), sa.ForeignKey("story_nodes.id"), nullable=True),
        sa.Column("thread_id", sa.String(), sa.ForeignKey("narrative_threads.id"), nullable=True),
        sa.Column("role_in_thread", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "narrative_elements",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_graph_run_id", sa.String(), sa.ForeignKey("story_graph_runs.id"), nullable=True),
        sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("element_type", sa.String(), nullable=True),
        sa.Column("first_seen_time", sa.Float(), nullable=True),
        sa.Column("last_seen_time", sa.Float(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("node_ids", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("narrative_elements")
    op.drop_table("node_thread_memberships")
    op.drop_table("narrative_threads")
    op.drop_table("story_edges")
    op.drop_table("story_nodes")
    op.drop_table("story_graph_runs")
