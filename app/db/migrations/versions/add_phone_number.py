"""
Add phone number field to User model

Revision ID: add_phone_number
Revises: 59821156b57d
Create Date: 2025-07-20 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_phone_number'
down_revision = '59821156b57d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add phone_number field to users table"""
    # Add phone_number column to users table
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
    
    # Add index for phone number for faster lookups
    op.create_index('ix_users_phone_number', 'users', ['phone_number'])


def downgrade() -> None:
    """Remove phone_number field from users table"""
    # Drop index
    op.drop_index('ix_users_phone_number', 'users')
    
    # Drop phone_number column
    op.drop_column('users', 'phone_number')
