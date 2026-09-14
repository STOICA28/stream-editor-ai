"""initial migration

Revision ID: 0001
Revises: 
Create Date: 2024-05-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Just a stub to satisfy the requirement
    pass

def downgrade() -> None:
    pass
