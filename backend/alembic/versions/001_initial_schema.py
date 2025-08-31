"""Initial schema with users, contacts, campaigns, messages, webhook_events

Revision ID: 001
Revises: 
Create Date: 2025-08-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for Attack-a-Crack v2."""
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('profile_image_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create indexes for users
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_name', 'users', ['name'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # Create contacts table
    op.create_table('contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('opted_out', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('opted_out_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number', 'user_id', name='uq_contacts_phone_user')
    )
    
    # Create indexes for contacts
    op.create_index('ix_contacts_id', 'contacts', ['id'])
    op.create_index('ix_contacts_phone_number', 'contacts', ['phone_number'])
    op.create_index('ix_contacts_name', 'contacts', ['name'])
    op.create_index('ix_contacts_email', 'contacts', ['email'])
    op.create_index('ix_contacts_opted_out', 'contacts', ['opted_out'])
    op.create_index('ix_contacts_user_id', 'contacts', ['user_id'])
    op.create_index('ix_contacts_created_at', 'contacts', ['created_at'])
    
    # Create campaigns table
    op.create_table('campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('message_template', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'scheduled', 'active', 'paused', 'completed', name='campaignstatus'), nullable=False, server_default='draft'),
        sa.Column('daily_limit', sa.Integer(), nullable=False, server_default='125'),
        sa.Column('total_limit', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for campaigns
    op.create_index('ix_campaigns_id', 'campaigns', ['id'])
    op.create_index('ix_campaigns_name', 'campaigns', ['name'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])
    op.create_index('ix_campaigns_start_date', 'campaigns', ['start_date'])
    op.create_index('ix_campaigns_end_date', 'campaigns', ['end_date'])
    op.create_index('ix_campaigns_user_id', 'campaigns', ['user_id'])
    op.create_index('ix_campaigns_created_at', 'campaigns', ['created_at'])
    
    # Create messages table
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('queued', 'sent', 'delivered', 'failed', name='messagestatus'), nullable=False, server_default='queued'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('openphone_message_id', sa.String(length=100), nullable=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for messages
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_status', 'messages', ['status'])
    op.create_index('ix_messages_sent_at', 'messages', ['sent_at'])
    op.create_index('ix_messages_delivered_at', 'messages', ['delivered_at'])
    op.create_index('ix_messages_openphone_message_id', 'messages', ['openphone_message_id'])
    op.create_index('ix_messages_campaign_id', 'messages', ['campaign_id'])
    op.create_index('ix_messages_contact_id', 'messages', ['contact_id'])
    
    # Create webhook_events table
    op.create_table('webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_error', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for webhook_events
    op.create_index('ix_webhook_events_id', 'webhook_events', ['id'])
    op.create_index('ix_webhook_events_event_type', 'webhook_events', ['event_type'])
    op.create_index('ix_webhook_events_processed', 'webhook_events', ['processed'])


def downgrade() -> None:
    """Drop all tables."""
    
    # Drop tables in reverse order due to foreign keys
    op.drop_table('webhook_events')
    op.drop_table('messages')
    op.drop_table('campaigns')
    op.drop_table('contacts')
    op.drop_table('users')
    
    # Drop custom enums
    op.execute("DROP TYPE IF EXISTS campaignstatus")
    op.execute("DROP TYPE IF EXISTS messagestatus")