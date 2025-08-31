"""
OpenPhone service for webhook signature validation and API interactions.

Handles HMAC-SHA256 signature validation for OpenPhone webhooks with replay attack protection.
"""

import hashlib
import hmac
import json
import time
from typing import Optional, Dict, Any

from app.core.config import Settings


def verify_webhook_signature(
    payload: str, 
    signature: str, 
    webhook_secret: str,
    timestamp: Optional[int] = None,
    tolerance: int = 300
) -> bool:
    """
    Verify OpenPhone webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw JSON payload as string
        signature: Signature from X-OpenPhone-Signature header
        webhook_secret: OpenPhone webhook secret from configuration
        timestamp: Optional timestamp from payload for replay protection
        tolerance: Timestamp tolerance in seconds (default: 5 minutes)
    
    Returns:
        bool: True if signature is valid and timestamp is within tolerance
    """
    if not payload or not signature or not webhook_secret:
        return False
    
    # Normalize signature format (handle different prefixes)
    normalized_signature = signature.lower()
    if normalized_signature.startswith('sha256='):
        normalized_signature = normalized_signature[7:]  # Remove 'sha256=' prefix
    
    # Compute expected signature
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(normalized_signature, expected_signature):
        return False
    
    # Validate timestamp if provided (replay attack prevention)
    if timestamp is not None:
        current_time = int(time.time())
        time_diff = abs(current_time - timestamp)
        
        if time_diff > tolerance:
            return False
    
    return True


def extract_timestamp_from_payload(payload_str: str) -> Optional[int]:
    """
    Extract timestamp from webhook payload for validation.
    
    Args:
        payload_str: Raw JSON payload as string
        
    Returns:
        Optional[int]: Timestamp if found, None otherwise
    """
    try:
        payload = json.loads(payload_str)
        
        # Try different possible timestamp field locations
        timestamp = (
            payload.get('timestamp') or
            payload.get('createdAt') or
            payload.get('data', {}).get('timestamp') or
            payload.get('data', {}).get('createdAt')
        )
        
        if timestamp:
            # Handle both Unix timestamps and ISO strings
            if isinstance(timestamp, str):
                from datetime import datetime
                try:
                    # Try parsing as ISO string
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return int(dt.timestamp())
                except (ValueError, AttributeError):
                    pass
            elif isinstance(timestamp, (int, float)):
                return int(timestamp)
    
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return None


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format.
    
    Args:
        phone: Raw phone number string
        
    Returns:
        str: Normalized phone number in E.164 format
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Add US country code if missing (assuming US numbers)
    if len(digits) == 10:
        digits = '1' + digits
    
    # Add + prefix for E.164 format
    if not digits.startswith('+'):
        digits = '+' + digits
    
    return digits


def validate_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize webhook payload structure.
    
    Args:
        payload: Parsed webhook payload
        
    Returns:
        Dict containing validation results and normalized data
    """
    result = {
        'valid': True,
        'errors': [],
        'normalized': payload.copy()
    }
    
    # Check required fields
    if 'type' not in payload:
        result['valid'] = False
        result['errors'].append('Missing required field: type')
    
    if 'data' not in payload:
        result['valid'] = False  
        result['errors'].append('Missing required field: data')
        return result
    
    data = payload['data']
    event_type = payload.get('type', '')
    
    # Validate based on event type
    if event_type.startswith('message.'):
        # Message events require messageId
        if 'messageId' not in data:
            result['valid'] = False
            result['errors'].append('Message events require messageId')
        
        # Normalize phone numbers if present
        if 'from' in data:
            result['normalized']['data']['from'] = normalize_phone_number(data['from'])
        if 'to' in data:
            result['normalized']['data']['to'] = normalize_phone_number(data['to'])
    
    elif event_type.startswith('call.'):
        # Call events require callId
        if 'callId' not in data:
            result['valid'] = False
            result['errors'].append('Call events require callId')
            
        # Normalize phone numbers
        if 'from' in data:
            result['normalized']['data']['from'] = normalize_phone_number(data['from'])
        if 'to' in data:
            result['normalized']['data']['to'] = normalize_phone_number(data['to'])
    
    elif event_type.startswith('voicemail.'):
        # Voicemail events require voicemailId
        if 'voicemailId' not in data:
            result['valid'] = False
            result['errors'].append('Voicemail events require voicemailId')
    
    return result


class OpenPhoneClient:
    """
    OpenPhone API client for making authenticated requests.
    
    Handles API key authentication and rate limiting.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openphone.com/v1"
    
    async def get_contact_info(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Fetch contact information from OpenPhone API.
        
        Args:
            phone_number: Phone number to look up
            
        Returns:
            Optional[Dict]: Contact info if found, None otherwise
        """
        # TODO: Implement when OpenPhone API integration is needed
        # This is a placeholder for future contact sync functionality
        pass
    
    async def send_sms(self, to: str, from_number: str, body: str) -> Dict[str, Any]:
        """
        Send SMS message via OpenPhone API.
        
        Args:
            to: Recipient phone number
            from_number: Sender phone number
            body: Message body
            
        Returns:
            Dict: API response with message details
        """
        # TODO: Implement when outbound SMS is needed
        # This is a placeholder for future SMS sending functionality
        pass