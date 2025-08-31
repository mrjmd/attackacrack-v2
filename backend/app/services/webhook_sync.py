"""
Synchronous webhook processing service for Celery tasks.

This module provides sync versions of webhook processing functions
that can be called from Celery tasks without async/await issues.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_sync_db
from app.models import Contact, Message, WebhookEvent, User
from app.models.message import MessageStatus, MessageType, MessageDirection
from app.services.openphone import normalize_phone_number

logger = logging.getLogger(__name__)


def get_or_create_system_user_sync(db: Session) -> User:
    """
    Get or create the system user for webhook-originated contacts.
    
    Sync version for Celery tasks.
    """
    system_email = "system@attackacrack.internal"
    
    # Try to find existing system user
    system_user = db.execute(
        select(User).where(User.email == system_email)
    ).scalar_one_or_none()
    
    if not system_user:
        # Create system user
        system_user = User(
            email=system_email,
            name="System (Webhook Contacts)",
            is_active=True
        )
        db.add(system_user)
        db.flush()  # Get the ID
    
    return system_user


def process_webhook_event_sync(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route webhook event to appropriate processor.
    
    Sync version for Celery tasks.
    """
    event_type = webhook_data.get('type', '')
    
    try:
        if event_type == 'message.received':
            return process_message_received_sync(webhook_data)
        elif event_type == 'message.delivered':
            return process_message_delivered_sync(webhook_data)
        elif event_type == 'message.sent':
            return process_message_sent_sync(webhook_data)
        elif event_type == 'message.failed':
            return process_message_failed_sync(webhook_data)
        elif event_type == 'call.completed':
            return process_call_completed_sync(webhook_data)
        elif event_type == 'call.missed':
            return process_call_missed_sync(webhook_data)
        elif event_type == 'voicemail.received':
            return process_voicemail_received_sync(webhook_data)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
            return {
                'status': 'ignored',
                'reason': 'unknown_event_type',
                'event_type': event_type
            }
    
    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'event_type': event_type
        }


def process_message_received_sync(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process incoming message webhook.
    
    Sync version for Celery tasks.
    """
    try:
        data = webhook_data.get('data', {})
        
        # Validate required fields
        if not data.get('messageId'):
            return {'status': 'invalid_data', 'error': 'Missing messageId'}
        
        if not data.get('from'):
            return {'status': 'invalid_data', 'error': 'Missing from phone number'}
        
        phone = normalize_phone_number(data['from'])
        message_id = data['messageId']
        body = data.get('body', '')
        to_phone = normalize_phone_number(data.get('to', ''))
        
        db = get_sync_db()
        try:
            # Check for duplicate message
            existing_message = db.execute(
                select(Message).where(Message.external_id == message_id)
            ).scalar_one_or_none()
            
            if existing_message:
                return {
                    'status': 'duplicate',
                    'message_created': False,
                    'message_id': message_id
                }
            
            # Find or create contact
            contact = db.execute(
                select(Contact).where(Contact.phone_number == phone)
            ).scalar_one_or_none()
            
            contact_created = False
            
            if not contact:
                # Get system user for webhook contacts
                system_user = get_or_create_system_user_sync(db)
                
                contact = Contact(
                    phone_number=phone,
                    user_id=system_user.id
                )
                db.add(contact)
                db.flush()  # Get the ID
                contact_created = True
            
            # Create message record
            message = Message(
                external_id=message_id,
                contact_id=contact.id,
                body=body,
                direction=MessageDirection.INBOUND,
                status=MessageStatus.RECEIVED,
                from_phone=phone,
                to_phone=to_phone,
                message_type=MessageType.SMS,
                received_at=datetime.now(timezone.utc)
            )
            db.add(message)
            
            db.commit()
            
            return {
                'status': 'processed',
                'contact_created': contact_created,
                'contact_id': contact.id,
                'message_created': True,
                'message_id': message_id
            }
    
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error processing message.received: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def process_message_delivered_sync(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process message delivered webhook.
    
    Sync version for Celery tasks.
    """
    try:
        data = webhook_data.get('data', {})
        message_id = data.get('messageId')
        
        if not message_id:
            return {'status': 'invalid_data', 'error': 'Missing messageId'}
        
        db = get_sync_db()
        try:
            # Find existing message
            message = db.execute(
                select(Message).where(Message.external_id == message_id)
            ).scalar_one_or_none()
            
            if not message:
                logger.warning(f"Message not found for delivery update: {message_id}")
                return {
                    'status': 'not_found',
                    'message_id': message_id,
                    'message_updated': False
                }
            
            # Update status
            message.status = MessageStatus.DELIVERED
            message.delivered_at = datetime.now(timezone.utc)
            
            db.commit()
            
            return {
                'status': 'processed',
                'message_updated': True,
                'message_id': message_id
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error processing message.delivered: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def process_message_sent_sync(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process message sent webhook.
    
    Sync version for Celery tasks.
    """
    try:
        data = webhook_data.get('data', {})
        message_id = data.get('messageId')
        
        if not message_id:
            return {'status': 'invalid_data', 'error': 'Missing messageId'}
        
        db = get_sync_db()
        try:
            message = db.execute(
                select(Message).where(Message.external_id == message_id)
            ).scalar_one_or_none()
            
            if message:
                message.status = MessageStatus.SENT
                message.sent_at = datetime.now(timezone.utc)
                db.commit()
                
                return {
                    'status': 'processed',
                    'message_updated': True,
                    'message_id': message_id
                }
            
            return {
                'status': 'not_found',
                'message_updated': False,
                'message_id': message_id
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error processing message.sent: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def process_message_failed_sync(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process message failed webhook.
    
    Sync version for Celery tasks.
    """
    try:
        data = webhook_data.get('data', {})
        message_id = data.get('messageId')
        error_message = data.get('error', {}).get('message', 'Unknown error')
        
        if not message_id:
            return {'status': 'invalid_data', 'error': 'Missing messageId'}
        
        db = get_sync_db()
        try:
            message = db.execute(
                select(Message).where(Message.external_id == message_id)
            ).scalar_one_or_none()
            
            if message:
                message.status = MessageStatus.FAILED
                message.error_message = error_message
                db.commit()
                
                return {
                    'status': 'processed',
                    'message_updated': True,
                    'message_id': message_id
                }
            
            return {
                'status': 'not_found',
                'message_updated': False,
                'message_id': message_id
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error processing message.failed: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def process_call_completed_sync(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process call completed webhook.
    
    Sync version for Celery tasks.
    """
    try:
        data = webhook_data.get('data', {})
        call_id = data.get('callId')
        phone = normalize_phone_number(data.get('from', ''))
        to_phone = normalize_phone_number(data.get('to', ''))
        duration = data.get('duration', 0)
        direction = data.get('direction', 'unknown')
        
        if not call_id or not phone:
            return {'status': 'invalid_data', 'error': 'Missing callId or phone number'}
        
        db = get_sync_db()
        try:
            # Find or create contact
            contact = db.execute(
                select(Contact).where(Contact.phone_number == phone)
            ).scalar_one_or_none()
            
            if not contact:
                # Get system user for webhook contacts
                system_user = get_or_create_system_user_sync(db)
                
                contact = Contact(
                    phone_number=phone,
                    user_id=system_user.id
                )
                db.add(contact)
                db.flush()
            
            # Create call record as Message with type=call
            recording_url = data.get('recording', {}).get('url', '')
            body = f"Call completed ({duration}s)"
            if recording_url:
                body += f" - Recording: {recording_url}"
            
            call_record = Message(
                external_id=call_id,
                contact_id=contact.id,
                body=body,
                direction=MessageDirection.INBOUND if direction == 'inbound' else MessageDirection.OUTBOUND,
                status=MessageStatus.COMPLETED,
                from_phone=phone,
                to_phone=to_phone,
                message_type=MessageType.CALL,
                duration_seconds=duration,
                received_at=datetime.now(timezone.utc)
            )
            db.add(call_record)
            
            db.commit()
            
            return {
                'status': 'processed',
                'call_created': True,
                'contact_id': contact.id,
                'call_id': call_id
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error processing call.completed: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def process_call_missed_sync(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process missed call webhook.
    
    Sync version for Celery tasks.
    """
    try:
        data = webhook_data.get('data', {})
        call_id = data.get('callId')
        phone = normalize_phone_number(data.get('from', ''))
        
        if not call_id or not phone:
            return {'status': 'invalid_data', 'error': 'Missing callId or phone number'}
        
        db = get_sync_db()
        try:
            # Find or create contact
            contact = db.execute(
                select(Contact).where(Contact.phone_number == phone)
            ).scalar_one_or_none()
            
            if not contact:
                # Get system user for webhook contacts
                system_user = get_or_create_system_user_sync(db)
                
                contact = Contact(
                    phone_number=phone,
                    user_id=system_user.id
                )
                db.add(contact)
                db.flush()
            
            # Create missed call record
            missed_call = Message(
                external_id=call_id,
                contact_id=contact.id,
                body="Missed call",
                direction=MessageDirection.INBOUND,
                status=MessageStatus.MISSED,
                from_phone=phone,
                to_phone=normalize_phone_number(data.get('to', '')),
                message_type=MessageType.CALL,
                received_at=datetime.now(timezone.utc)
            )
            db.add(missed_call)
            
            db.commit()
            
            return {
                'status': 'processed',
                'call_created': True,
                'contact_id': contact.id,
                'call_id': call_id
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error processing call.missed: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def process_voicemail_received_sync(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process voicemail received webhook.
    
    Sync version for Celery tasks.
    """
    try:
        data = webhook_data.get('data', {})
        voicemail_id = data.get('voicemailId')
        phone = normalize_phone_number(data.get('from', ''))
        transcript = data.get('transcript', '')
        duration = data.get('duration', 0)
        
        if not voicemail_id or not phone:
            return {'status': 'invalid_data', 'error': 'Missing voicemailId or phone number'}
        
        db = get_sync_db()
        try:
            # Find or create contact
            contact = db.execute(
                select(Contact).where(Contact.phone_number == phone)
            ).scalar_one_or_none()
            
            if not contact:
                # Get system user for webhook contacts
                system_user = get_or_create_system_user_sync(db)
                
                contact = Contact(
                    phone_number=phone,
                    user_id=system_user.id
                )
                db.add(contact)
                db.flush()
            
            # Create voicemail record
            recording_url = data.get('recording', {}).get('url', '')
            body = transcript or f"Voicemail ({duration}s)"
            if recording_url:
                body += f" - Recording: {recording_url}"
            
            voicemail = Message(
                external_id=voicemail_id,
                contact_id=contact.id,
                body=body,
                direction=MessageDirection.INBOUND,
                status=MessageStatus.RECEIVED,
                from_phone=phone,
                to_phone=normalize_phone_number(data.get('to', '')),
                message_type=MessageType.VOICEMAIL,
                duration_seconds=duration,
                received_at=datetime.now(timezone.utc)
            )
            db.add(voicemail)
            
            db.commit()
            
            return {
                'status': 'processed',
                'voicemail_created': True,
                'contact_id': contact.id,
                'voicemail_id': voicemail_id
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error processing voicemail.received: {str(e)}")
        return {'status': 'error', 'error': str(e)}


def handle_failed_webhook_sync(webhook_data: Dict[str, Any], error: str) -> None:
    """
    Handle webhook that failed processing after all retries.
    
    Sync version for Celery tasks.
    """
    try:
        db = get_sync_db()
        try:
            # Find webhook event record if it exists
            event_type = webhook_data.get('type', 'unknown')
            
            webhook_event = db.execute(
                select(WebhookEvent).where(
                    WebhookEvent.event_type == event_type
                ).where(
                    WebhookEvent.payload == webhook_data
                ).order_by(WebhookEvent.created_at.desc())
            ).first()
            
            if webhook_event:
                webhook_event[0].mark_failed(error)
                db.commit()
                
                logger.error(f"Webhook permanently failed: {event_type} - {error}")
            else:
                # Create new failed webhook record
                failed_event = WebhookEvent(
                    event_type=event_type,
                    payload=webhook_data,
                    processed=False
                )
                failed_event.mark_failed(f"Failed after retries: {error}")
                
                db.add(failed_event)
                db.commit()
                
                logger.error(f"Created failed webhook record: {event_type} - {error}")
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error handling failed webhook: {str(e)}")