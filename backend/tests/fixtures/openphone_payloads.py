"""
Realistic OpenPhone webhook payload examples for testing.

These are based on actual OpenPhone API webhook formats and will be used
across multiple test files for consistent testing.
"""

from datetime import datetime, timezone
from typing import Dict, Any


class OpenPhonePayloads:
    """Container for realistic OpenPhone webhook payloads."""
    
    @staticmethod
    def message_received(
        message_id: str = "msg_test_123",
        from_phone: str = "+15551234567",
        to_phone: str = "+15559876543",
        body: str = "Hello, I need help with my foundation crack"
    ) -> Dict[str, Any]:
        """Realistic message.received webhook payload."""
        return {
            "type": "message.received",
            "data": {
                "messageId": message_id,
                "from": from_phone,
                "to": to_phone,
                "body": body,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "direction": "inbound",
                "status": "received",
                "phoneNumber": to_phone,  # The OpenPhone number
                "contact": {
                    "id": f"contact_{hash(from_phone) % 10000}",
                    "phoneNumber": from_phone,
                    "name": None  # Usually null for new contacts
                },
                "conversation": {
                    "id": f"conv_{hash(from_phone + to_phone) % 10000}",
                    "phoneNumbers": [from_phone, to_phone]
                }
            }
        }
    
    @staticmethod
    def message_delivered(
        message_id: str = "msg_delivery_123",
        delivered_at: str = None
    ) -> Dict[str, Any]:
        """Realistic message.delivered webhook payload."""
        if delivered_at is None:
            delivered_at = datetime.now(timezone.utc).isoformat()
        
        return {
            "type": "message.delivered",
            "data": {
                "messageId": message_id,
                "status": "delivered",
                "deliveredAt": delivered_at,
                "phoneNumber": "+15559876543"  # The OpenPhone number
            }
        }
    
    @staticmethod
    def message_failed(
        message_id: str = "msg_failed_123",
        error_code: str = "RATE_LIMIT_EXCEEDED"
    ) -> Dict[str, Any]:
        """Realistic message.failed webhook payload."""
        return {
            "type": "message.failed",
            "data": {
                "messageId": message_id,
                "status": "failed",
                "failedAt": datetime.now(timezone.utc).isoformat(),
                "error": {
                    "code": error_code,
                    "message": "Message sending failed due to rate limiting"
                },
                "phoneNumber": "+15559876543"
            }
        }
    
    @staticmethod
    def call_completed(
        call_id: str = "call_test_456",
        from_phone: str = "+15551234567", 
        to_phone: str = "+15559876543",
        duration: int = 180,
        direction: str = "inbound"
    ) -> Dict[str, Any]:
        """Realistic call.completed webhook payload."""
        return {
            "type": "call.completed",
            "data": {
                "callId": call_id,
                "from": from_phone,
                "to": to_phone,
                "direction": direction,
                "status": "completed",
                "duration": duration,  # seconds
                "startedAt": datetime.now(timezone.utc).isoformat(),
                "completedAt": datetime.now(timezone.utc).isoformat(),
                "phoneNumber": to_phone if direction == "inbound" else from_phone,
                "recording": {
                    "id": f"rec_{call_id}",
                    "url": f"https://recordings.openphone.com/{call_id}.mp3",
                    "duration": duration
                } if duration > 30 else None,  # Only record calls > 30s
                "contact": {
                    "id": f"contact_{hash(from_phone) % 10000}",
                    "phoneNumber": from_phone if direction == "inbound" else to_phone
                }
            }
        }
    
    @staticmethod
    def call_missed(
        call_id: str = "call_missed_789",
        from_phone: str = "+15551234567",
        to_phone: str = "+15559876543"
    ) -> Dict[str, Any]:
        """Realistic call.missed webhook payload."""
        return {
            "type": "call.missed",
            "data": {
                "callId": call_id,
                "from": from_phone,
                "to": to_phone,
                "direction": "inbound",
                "status": "missed",
                "duration": 0,
                "startedAt": datetime.now(timezone.utc).isoformat(),
                "missedAt": datetime.now(timezone.utc).isoformat(),
                "phoneNumber": to_phone,
                "contact": {
                    "id": f"contact_{hash(from_phone) % 10000}",
                    "phoneNumber": from_phone
                }
            }
        }
    
    @staticmethod
    def voicemail_received(
        voicemail_id: str = "vm_test_101112",
        from_phone: str = "+15551234567",
        to_phone: str = "+15559876543", 
        duration: int = 45,
        transcript: str = "Hi, this is John Smith calling about the foundation crack repair. Please call me back at your earliest convenience."
    ) -> Dict[str, Any]:
        """Realistic voicemail.received webhook payload."""
        return {
            "type": "voicemail.received",
            "data": {
                "voicemailId": voicemail_id,
                "from": from_phone,
                "to": to_phone,
                "duration": duration,
                "receivedAt": datetime.now(timezone.utc).isoformat(),
                "phoneNumber": to_phone,
                "transcript": {
                    "text": transcript,
                    "confidence": 0.95
                },
                "recording": {
                    "id": f"rec_{voicemail_id}",
                    "url": f"https://recordings.openphone.com/{voicemail_id}.mp3",
                    "duration": duration
                },
                "contact": {
                    "id": f"contact_{hash(from_phone) % 10000}",
                    "phoneNumber": from_phone
                }
            }
        }
    
    @staticmethod
    def call_started(
        call_id: str = "call_started_131415",
        from_phone: str = "+15551234567",
        to_phone: str = "+15559876543",
        direction: str = "inbound"
    ) -> Dict[str, Any]:
        """Realistic call.started webhook payload."""
        return {
            "type": "call.started", 
            "data": {
                "callId": call_id,
                "from": from_phone,
                "to": to_phone,
                "direction": direction,
                "status": "ringing",
                "startedAt": datetime.now(timezone.utc).isoformat(),
                "phoneNumber": to_phone if direction == "inbound" else from_phone,
                "contact": {
                    "id": f"contact_{hash(from_phone) % 10000}",
                    "phoneNumber": from_phone if direction == "inbound" else to_phone
                }
            }
        }
    
    @staticmethod
    def transcript_ready(
        call_id: str = "call_transcript_161718",
        transcript_text: str = "Customer discussed foundation crack issues on north wall. Mentioned previous water damage. Wants estimate for waterproofing.",
        confidence: float = 0.92
    ) -> Dict[str, Any]:
        """Realistic transcript.ready webhook payload."""
        return {
            "type": "transcript.ready",
            "data": {
                "callId": call_id,
                "transcriptId": f"transcript_{call_id}",
                "transcript": {
                    "text": transcript_text,
                    "confidence": confidence,
                    "language": "en-US"
                },
                "processedAt": datetime.now(timezone.utc).isoformat()
            }
        }
    
    @staticmethod
    def summary_ready(
        call_id: str = "call_summary_192021",
        summary_text: str = "Customer inquiry about foundation waterproofing. Needs estimate for north wall repair.",
        key_points: list = None
    ) -> Dict[str, Any]:
        """Realistic summary.ready webhook payload.""" 
        if key_points is None:
            key_points = [
                "Foundation crack on north wall",
                "Previous water damage",
                "Requesting repair estimate",
                "Available weekdays after 3pm"
            ]
        
        return {
            "type": "summary.ready",
            "data": {
                "callId": call_id,
                "summaryId": f"summary_{call_id}",
                "summary": {
                    "text": summary_text,
                    "keyPoints": key_points,
                    "sentiment": "neutral",
                    "priority": "medium"
                },
                "processedAt": datetime.now(timezone.utc).isoformat()
            }
        }


# Common test scenarios
TEST_SCENARIOS = {
    "new_customer_inquiry": OpenPhonePayloads.message_received(
        message_id="msg_new_inquiry",
        from_phone="+15551111111",
        body="Hi, I have a crack in my basement wall that's leaking water. Can you help?"
    ),
    
    "existing_customer_followup": OpenPhonePayloads.message_received(
        message_id="msg_followup",
        from_phone="+15552222222", 
        body="Thanks for the estimate. When can you schedule the work?"
    ),
    
    "urgent_call_missed": OpenPhonePayloads.call_missed(
        call_id="call_urgent",
        from_phone="+15553333333"
    ),
    
    "detailed_voicemail": OpenPhonePayloads.voicemail_received(
        voicemail_id="vm_detailed",
        transcript="Hi, this is Sarah Johnson at 123 Oak Street. I have a serious foundation issue with water coming through my basement wall. I've been getting quotes and would like to discuss your services. My number is 555-333-3333. Please call me back today if possible, this is urgent."
    ),
    
    "long_consultation_call": OpenPhonePayloads.call_completed(
        call_id="call_consultation",
        duration=1200,  # 20 minutes
        direction="inbound"
    )
}


# Invalid payload examples for testing error handling
INVALID_PAYLOADS = {
    "missing_type": {
        "data": {"messageId": "test"}
    },
    
    "missing_data": {
        "type": "message.received"
    },
    
    "invalid_phone": OpenPhonePayloads.message_received(
        from_phone="invalid_phone_number"
    ),
    
    "empty_body": OpenPhonePayloads.message_received(
        body=""
    ),
    
    "malformed_timestamp": {
        "type": "message.received",
        "data": {
            "messageId": "test",
            "createdAt": "not_a_timestamp"
        }
    }
}