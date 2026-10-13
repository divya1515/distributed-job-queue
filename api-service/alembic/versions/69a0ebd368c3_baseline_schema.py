"""baseline schema

Revision ID: 69a0ebd368c3
Revises: 
Create Date: 2026-09-19 10:47:36.038288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '69a0ebd368c3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'job',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('type', sa.Enum('bulk_url_shortening', name='jobtype'), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'partial_failure', 'completed', 'failed', name='jobstatus'), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=False),
        sa.Column('completed_items', sa.Integer(), nullable=False),
        sa.Column('failed_items', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id'),
    )
    op.create_index(op.f('ix_job_status'), 'job', ['status'], unique=False)
    op.create_table(
        'job_item',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('job_id', sa.BigInteger(), nullable=False),
        sa.Column('item_index', sa.BigInteger(), nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('short_url', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'success', 'failed', 'dead_letter', name='jobitemstatus'), nullable=False),
        sa.Column('attempts', sa.BigInteger(), nullable=False),
        sa.Column('max_attempts', sa.BigInteger(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['job.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_job_item_job_status', 'job_item', ['job_id', 'status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_job_item_job_status', table_name='job_item')
    op.drop_table('job_item')
    op.drop_index(op.f('ix_job_status'), table_name='job')
    op.drop_table('job')
    sa.Enum(name='jobitemstatus').drop(op.get_bind())
    sa.Enum(name='jobstatus').drop(op.get_bind())
    sa.Enum(name='jobtype').drop(op.get_bind())
