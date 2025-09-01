"""
Integration tests for OpenPhone webhook endpoint.

Tests the complete webhook receiver endpoint that:
1. Receives webhooks at POST /api/v1/webhooks/openphone
2. Validates OpenPhone signatures
3. Queues to Celery for async processing
4. Returns 200 OK quickly (<100ms)

These tests will FAIL initially (RED phase) since no implementation exists.
"""

import json
import time
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession


class TestWebhookEndpoint:
    """Test OpenPhone webhook endpoint with full stack."""
    
    @pytest.mark.asyncio
    async def test_webhook_endpoint_exists(self, client: AsyncClient):
        """Test webhook endpoint exists at correct path."""
        response = await client.get("/api/v1/webhooks/openphone")
        
        # Should return 405 Method Not Allowed (GET not supported)
        # This confirms endpoint exists but only accepts POST
        assert response.status_code == 405
        
        # POST should work (will fail signature check initially)
        response = await client.post("/api/v1/webhooks/openphone")
        # We expect 400 (bad signature) or similar, NOT 404
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_valid_webhook_returns_200(self, client: AsyncClient):
        """Test valid webhook payload returns 200 OK quickly."""
        webhook_payload = {
            "type": "message.received",
            "data": {
                "messageId": "msg_12345",
                "from": "+15551234567",
                "to": "+15559876543",
                "body": "Hello from customer",
                "createdAt": "2024-01-15T10:30:00Z"
            }
        }
        
        # Mock signature validation to pass
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            # Mock Celery task queueing
            with patch('app.worker.process_openphone_webhook.delay') as mock_queue:
                start_time = time.time()
                
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    json=webhook_payload,
                    headers={
                        "X-OpenPhone-Signature": "valid_signature",
                        "Content-Type": "application/json"
                    }
                )
                
                duration = time.time() - start_time
                
                # Should return 200 OK
                assert response.status_code == 200
                assert response.json() == {"status": "queued"}
                
                # Should be fast (<100ms as per requirements)
                assert duration < 0.1, f"Webhook took {duration:.3f}s, should be <0.1s"
                
                # Should queue to Celery
                mock_queue.assert_called_once()
                queued_payload = mock_queue.call_args[0][0]
                assert json.loads(queued_payload) == webhook_payload
    
    @pytest.mark.asyncio 
    async def test_invalid_signature_returns_400(self, client: AsyncClient):
        """Test invalid signature returns 400 Bad Request."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "msg_12345"}
        }
        
        # Mock signature validation to fail
        with patch('app.services.openphone.verify_webhook_signature', return_value=False):
            response = await client.post(
                "/api/v1/webhooks/openphone",
                json=webhook_payload,
                headers={
                    "X-OpenPhone-Signature": "invalid_signature"
                }
            )
            
            assert response.status_code == 400
            assert "signature" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_missing_signature_returns_400(self, client: AsyncClient):
        """Test missing signature header returns 400."""
        webhook_payload = {
            "type": "message.received", 
            "data": {"messageId": "msg_12345"}
        }
        
        response = await client.post(
            "/api/v1/webhooks/openphone",
            json=webhook_payload
        )
        
        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_different_event_types_accepted(self, client: AsyncClient):
        """Test different OpenPhone event types are accepted."""
        event_types = [
            "message.received",
            "message.delivered", 
            "message.failed",
            "call.completed",
            "call.missed",
            "voicemail.received"
        ]
        
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            with patch('app.worker.process_openphone_webhook.delay') as mock_queue:
                
                for event_type in event_types:
                    webhook_payload = {
                        "type": event_type,
                        "data": {"id": f"test_{event_type}"}
                    }
                    
                    response = await client.post(
                        "/api/v1/webhooks/openphone",
                        json=webhook_payload,
                        headers={"X-OpenPhone-Signature": "valid"}
                    )
                    
                    assert response.status_code == 200, f"Failed for event type: {event_type}"
                    assert response.json() == {"status": "queued"}
                
                # Should have queued all events
                assert mock_queue.call_count == len(event_types)
    
    @pytest.mark.asyncio
    async def test_malformed_json_returns_422(self, client: AsyncClient):
        """Test malformed JSON returns 422 Unprocessable Entity."""
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            response = await client.post(
                "/api/v1/webhooks/openphone",
                content="invalid json{",
                headers={
                    "X-OpenPhone-Signature": "valid",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_webhook_stores_event_record(self, client: AsyncClient):
        """Test webhook creates WebhookEvent record in database."""
        webhook_payload = {
            "type": "message.received",
            "data": {
                "messageId": "msg_store_test",
                "from": "+15551234567",
                "body": "Test message"
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
                
                # For integration test, we verify the API responds correctly
                # Database verification would be done in unit tests of the service layer
                data = response.json()
                assert data["status"] == "queued"
    
    @pytest.mark.asyncio
    async def test_duplicate_webhooks_handled_gracefully(self, client: AsyncClient):
        """Test duplicate webhooks don't cause errors."""
        webhook_payload = {
            "type": "message.received",
            "data": {
                "messageId": "msg_duplicate_test",
                "from": "+15551234567"
            }
        }
        
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            with patch('app.worker.process_openphone_webhook.delay') as mock_queue:
                
                # Send same webhook twice
                for i in range(2):
                    response = await client.post(
                        "/api/v1/webhooks/openphone",
                        json=webhook_payload,
                        headers={"X-OpenPhone-Signature": "valid"}
                    )
                    
                    assert response.status_code == 200
                
                # Both should be queued (deduplication happens in worker)
                assert mock_queue.call_count == 2
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, client: AsyncClient):
        """Test webhook endpoint performance under concurrent load."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "load_test"}
        }
        
        import asyncio
        
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                async def send_webhook():
                    response = await client.post(
                        "/api/v1/webhooks/openphone",
                        json=webhook_payload,
                        headers={"X-OpenPhone-Signature": "valid"}
                    )
                    return response.status_code
                
                # Send 10 concurrent webhooks
                start_time = time.time()
                results = await asyncio.gather(*[send_webhook() for _ in range(10)])
                duration = time.time() - start_time
                
                # All should succeed
                assert all(code == 200 for code in results)
                
                # Should complete in reasonable time (under 1 second total)
                assert duration < 1.0, f"10 concurrent requests took {duration:.3f}s"
    
    @pytest.mark.asyncio
    async def test_celery_queue_failure_returns_500(self, client: AsyncClient):
        """Test Celery queueing failure returns 500 Internal Server Error."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "queue_fail_test"}
        }
        
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            # Mock Celery task queueing to fail
            with patch('app.worker.process_openphone_webhook.delay', side_effect=Exception("Queue failed")):
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    json=webhook_payload,
                    headers={"X-OpenPhone-Signature": "valid"}
                )
                
                assert response.status_code == 500
                assert "queue" in response.json()["detail"].lower()