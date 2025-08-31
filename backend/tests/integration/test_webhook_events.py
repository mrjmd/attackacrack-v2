"""
Event processing tests for OpenPhone webhooks.

Tests webhook event handling:
1. message.received creates WebhookEvent record
2. Contact created/updated from phone number 
3. Message record created with correct status
4. Handles duplicate webhooks gracefully
5. Processes different event types correctly

These tests will FAIL initially (RED phase) since no implementation exists.
"""

import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import patch
from datetime import datetime, timezone
from app.models.message import MessageDirection, MessageStatus, MessageType


class TestWebhookEventProcessing:
    """Test webhook event processing and database updates."""
    
    @pytest.mark.asyncio
    async def test_message_received_creates_webhook_event(self, client: AsyncClient, db_session: AsyncSession):
        """Test message.received webhook creates WebhookEvent record."""
        webhook_payload = {
            "type": "message.received",
            "data": {
                "messageId": "msg_webhook_event_test",
                "from": "+15551234567",
                "to": "+15559876543", 
                "body": "Hello webhook event test",
                "createdAt": "2024-01-15T10:30:00Z"
            }
        }
        
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    json=webhook_payload,
                    headers={"X-OpenPhone-Signature": "valid"}
                )
                
                assert response.status_code == 200
                
                # Check WebhookEvent was created
                from app.models import WebhookEvent
                result = await db_session.execute(
                    select(WebhookEvent).where(WebhookEvent.event_type == "message.received")
                )
                webhook_event = result.scalar_one_or_none()
                
                assert webhook_event is not None
                assert webhook_event.event_type == "message.received"
                assert webhook_event.payload == webhook_payload
                assert webhook_event.processed is False
                assert webhook_event.get_message_id() == "msg_webhook_event_test"
                assert webhook_event.get_phone_number() == "+15551234567"
    
    @pytest.mark.asyncio
    async def test_contact_created_from_phone_number(self, db_session: AsyncSession):
        """Test contact is created when processing message from new phone number."""
        from app.services.webhook import process_message_received
        
        webhook_data = {
            "type": "message.received",
            "data": {
                "messageId": "msg_new_contact",
                "from": "+15551111111",  # New phone number
                "to": "+15559876543",
                "body": "First message from new contact",
                "createdAt": "2024-01-15T10:30:00Z"
            }
        }
        
        # Test the webhook service function directly - it uses its own database session
        with patch('app.services.webhook.SessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            result = await process_message_received(webhook_data)
            
            # Should create contact
            from app.models import Contact
            contact_result = await db_session.execute(
                select(Contact).where(Contact.phone_number == "+15551111111")
            )
            contact = contact_result.scalar_one_or_none()
            
            assert contact is not None
            assert contact.phone_number == "+15551111111"
            assert contact.name is None  # No name extracted yet
            assert result["status"] == "processed"
            assert result["contact_created"] is True
    
    @pytest.mark.asyncio
    async def test_existing_contact_updated(self, db_session: AsyncSession, test_user):
        """Test existing contact is found and message associated."""
        # Create existing contact
        from app.models import Contact
        existing_contact = Contact(
            phone_number="+15552222222",
            name="Existing Customer",
            user_id=test_user.id
        )
        db_session.add(existing_contact)
        await db_session.commit()
        
        from app.services.webhook import process_message_received
        
        webhook_data = {
            "type": "message.received",
            "data": {
                "messageId": "msg_existing_contact",
                "from": "+15552222222",  # Existing contact
                "to": "+15559876543",
                "body": "Follow-up message",
                "createdAt": "2024-01-15T11:00:00Z"
            }
        }
        
        # Test the webhook service function directly - it uses its own database session
        with patch('app.services.webhook.SessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            result = await process_message_received(webhook_data)
            
            # Should find existing contact
            await db_session.refresh(existing_contact)
            assert existing_contact.name == "Existing Customer"  # Unchanged
            assert result["status"] == "processed"
            assert result["contact_created"] is False
            assert result["contact_id"] == existing_contact.id
    
    @pytest.mark.asyncio
    async def test_message_record_created_with_correct_status(self, db_session: AsyncSession):
        """Test Message record is created with correct status and data."""
        from app.services.webhook import process_message_received
        
        webhook_data = {
            "type": "message.received", 
            "data": {
                "messageId": "msg_record_test",
                "from": "+15553333333",
                "to": "+15559876543",
                "body": "Test message record creation",
                "createdAt": "2024-01-15T12:00:00Z"
            }
        }
        
        # Test the webhook service function directly - it uses its own database session
        with patch('app.services.webhook.SessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            result = await process_message_received(webhook_data)
            
            # Check Message record was created
            from app.models import Message
            message_result = await db_session.execute(
                select(Message).where(Message.external_id == "msg_record_test")
            )
            message = message_result.scalar_one_or_none()
            
            assert message is not None
            assert message.external_id == "msg_record_test"
            assert message.body == "Test message record creation"
            assert message.direction.value == "inbound"
            assert message.status.value == "received"
            assert message.from_phone == "+15553333333"
            assert message.to_phone == "+15559876543"
            assert result["message_created"] is True
    
    @pytest.mark.asyncio
    async def test_duplicate_message_handled_gracefully(self, db_session: AsyncSession, test_user):
        """Test duplicate message webhooks don't create duplicate records."""
        # Create existing message
        from app.models import Message, Contact
        
        contact = Contact(
            phone_number="+15554444444",
            user_id=test_user.id
        )
        db_session.add(contact)
        await db_session.flush()
        
        existing_message = Message(
            external_id="msg_duplicate_test",
            contact_id=contact.id,
            body="Original message",
            direction=MessageDirection.INBOUND,
            status=MessageStatus.RECEIVED,
            from_phone="+15554444444",
            to_phone="+15559876543"
        )
        db_session.add(existing_message)
        await db_session.commit()
        
        from app.services.webhook import process_message_received
        
        webhook_data = {
            "type": "message.received",
            "data": {
                "messageId": "msg_duplicate_test",  # Same as existing
                "from": "+15554444444",
                "to": "+15559876543", 
                "body": "Duplicate message attempt",
                "createdAt": "2024-01-15T13:00:00Z"
            }
        }
        
        # Test the webhook service function directly - it uses its own database session
        with patch('app.services.webhook.SessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            result = await process_message_received(webhook_data)
            
            # Should handle gracefully without creating duplicate
            assert result["status"] == "duplicate"
            assert result["message_created"] is False
            
            # Should only have one message with this external_id
            from sqlalchemy import func
            count_result = await db_session.execute(
                select(func.count(Message.id)).where(Message.external_id == "msg_duplicate_test")
            )
            count = count_result.scalar()
            assert count == 1
    
    @pytest.mark.asyncio
    async def test_message_delivered_updates_status(self, db_session: AsyncSession, test_user):
        """Test message.delivered webhook updates existing message status."""
        # Create existing outbound message
        from app.models import Message, Contact
        
        contact = Contact(
            phone_number="+15555555555",
            user_id=test_user.id
        )
        db_session.add(contact)
        await db_session.flush()
        
        outbound_message = Message(
            external_id="msg_delivery_test",
            contact_id=contact.id,
            body="Test delivery update",
            direction=MessageDirection.OUTBOUND, 
            status=MessageStatus.SENT,
            from_phone="+15559876543",
            to_phone="+15555555555"
        )
        db_session.add(outbound_message)
        await db_session.commit()
        
        from app.services.webhook import process_message_delivered
        
        webhook_data = {
            "type": "message.delivered",
            "data": {
                "messageId": "msg_delivery_test",
                "deliveredAt": "2024-01-15T14:00:00Z"
            }
        }
        
        # Test the webhook service function directly - it uses its own database session
        with patch('app.services.webhook.SessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            result = await process_message_delivered(webhook_data)
            
            # Should update message status
            await db_session.refresh(outbound_message)
            assert outbound_message.status == MessageStatus.DELIVERED
            assert result["status"] == "processed"
            assert result["message_updated"] is True
    
    @pytest.mark.asyncio
    async def test_call_completed_creates_call_record(self, db_session: AsyncSession):
        """Test call.completed webhook creates call activity record."""
        from app.services.webhook import process_call_completed
        
        webhook_data = {
            "type": "call.completed",
            "data": {
                "callId": "call_12345",
                "from": "+15556666666", 
                "to": "+15559876543",
                "direction": "inbound",
                "duration": 180,  # 3 minutes
                "completedAt": "2024-01-15T15:00:00Z",
                "recording": {
                    "url": "https://openphone.com/recordings/call_12345.mp3"
                }
            }
        }
        
        # Test the webhook service function directly - it uses its own database session
        with patch('app.services.webhook.SessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            result = await process_call_completed(webhook_data)
            
            # Should create contact if doesn't exist
            from app.models import Contact
            contact_result = await db_session.execute(
                select(Contact).where(Contact.phone_number == "+15556666666")
            )
            contact = contact_result.scalar_one_or_none()
            assert contact is not None
            
            # Should create call activity (Message record with type=call)
            from app.models import Message
            call_result = await db_session.execute(
                select(Message).where(
                    Message.external_id == "call_12345"
                ).where(Message.message_type == MessageType.CALL)
            )
            call_record = call_result.scalar_one_or_none()
            
            assert call_record is not None
            assert call_record.external_id == "call_12345"
            assert call_record.direction.value == "inbound"
            assert call_record.duration_seconds == 180
            assert "recordings/call_12345.mp3" in call_record.body  # Recording URL stored
            assert result["call_created"] is True
    
    @pytest.mark.asyncio
    async def test_voicemail_received_creates_message(self, db_session: AsyncSession):
        """Test voicemail.received webhook creates voicemail message record."""
        from app.services.webhook import process_voicemail_received
        
        webhook_data = {
            "type": "voicemail.received",
            "data": {
                "voicemailId": "vm_67890",
                "from": "+15557777777",
                "to": "+15559876543", 
                "duration": 45,  # 45 seconds
                "receivedAt": "2024-01-15T16:00:00Z",
                "transcript": "Hi, this is John calling about the foundation issue...",
                "recording": {
                    "url": "https://openphone.com/voicemails/vm_67890.mp3"
                }
            }
        }
        
        # Test the webhook service function directly - it uses its own database session
        with patch('app.services.webhook.SessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            result = await process_voicemail_received(webhook_data)
            
            # Should create voicemail message
            from app.models import Message
            vm_result = await db_session.execute(
                select(Message).where(
                    Message.external_id == "vm_67890"
                ).where(Message.message_type == MessageType.VOICEMAIL)
            )
            voicemail = vm_result.scalar_one_or_none()
            
            assert voicemail is not None
            assert voicemail.external_id == "vm_67890"
            # Body should contain transcript and recording URL
            assert "Hi, this is John calling about the foundation issue..." in voicemail.body
            assert "Recording: https://openphone.com/voicemails/vm_67890.mp3" in voicemail.body
            assert voicemail.direction.value == "inbound"
            assert voicemail.duration_seconds == 45
            assert result["voicemail_created"] is True
    
    @pytest.mark.asyncio
    async def test_unknown_event_type_handled_gracefully(self, db_session: AsyncSession):
        """Test unknown webhook event types are logged but don't cause errors."""
        from app.services.webhook import process_webhook_event
        
        webhook_data = {
            "type": "unknown.event.type",
            "data": {
                "someId": "unknown_test",
                "someData": "Should be logged but not processed"
            }
        }
        
        # This test doesn't require database patching since it's an unknown event type
        with patch('app.services.webhook.logger') as mock_logger:
            
            result = await process_webhook_event(webhook_data)
            
            # Should handle gracefully
            assert result["status"] == "ignored"
            assert result["reason"] == "unknown_event_type"
            
            # Should log the unknown event
            mock_logger.warning.assert_called()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "unknown.event.type" in warning_msg
    
    @pytest.mark.asyncio
    async def test_malformed_webhook_data_handled_safely(self, db_session: AsyncSession):
        """Test malformed webhook data doesn't crash processing."""
        from app.services.webhook import process_message_received
        
        malformed_cases = [
            # Missing required fields
            {"type": "message.received", "data": {}},
            
            # Missing data section
            {"type": "message.received"},
            
            # Missing messageId
            {
                "type": "message.received",
                "data": {
                    "from": "+15558888888",
                    "body": "Test"
                }
            },
            
            # Missing from phone
            {
                "type": "message.received",
                "data": {
                    "messageId": "test_123",
                    "body": "Test"
                }
            }
        ]
        
        # Test malformed data handling - some tests may need database, patch SessionLocal just in case
        with patch('app.services.webhook.SessionLocal') as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session
            mock_session_local.return_value.__aexit__.return_value = None
            
            for malformed_data in malformed_cases:
                result = await process_message_received(malformed_data)
                
                # Should handle gracefully without exceptions
                assert result["status"] in ["error", "invalid_data"]
                assert "error" in result  # Should include error description