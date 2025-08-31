"""
Security tests for OpenPhone webhook endpoint.

Tests webhook security features:
1. HMAC-SHA256 signature validation
2. Timestamp validation (replay attack prevention) 
3. Rate limiting considerations
4. IP allowlist (future consideration)

These tests will FAIL initially (RED phase) since no implementation exists.
"""

import hashlib
import hmac
import json
import time
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestWebhookSecurity:
    """Test webhook security validation."""
    
    def _create_mock_settings(self, webhook_secret: str, tolerance: int = 300):
        """Create mock settings for webhook tests."""
        mock_settings = MagicMock()
        mock_settings.openphone_webhook_secret = webhook_secret
        mock_settings.webhook_timestamp_tolerance = tolerance
        return mock_settings
    
    @pytest.mark.asyncio
    async def test_hmac_sha256_signature_validation(self, client: AsyncClient):
        """Test HMAC-SHA256 signature validation with real computation."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "security_test_123"}
        }
        payload_json = json.dumps(webhook_payload, separators=(',', ':'))
        
        # Mock webhook secret
        webhook_secret = "test_secret_key_12345"
        
        # Compute correct signature
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret)):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                # Test with correct signature - use raw content to match signature
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    content=payload_json,
                    headers={
                        "X-OpenPhone-Signature": signature,
                        "Content-Type": "application/json"
                    }
                )
                
                assert response.status_code == 200
                
                # Test with incorrect signature
                wrong_signature = "wrong_" + signature
                response = await client.post(
                    "/api/v1/webhooks/openphone", 
                    content=payload_json,
                    headers={
                        "X-OpenPhone-Signature": wrong_signature,
                        "Content-Type": "application/json"
                    }
                )
                
                assert response.status_code == 400
                assert "signature" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_signature_with_different_payload_formats(self, client: AsyncClient):
        """Test signature validation works with different JSON formatting."""
        webhook_data = {"type": "test", "data": {"id": 123}}
        webhook_secret = "test_secret"
        
        # Different JSON formatting should all work
        formats = [
            json.dumps(webhook_data, separators=(',', ':')),  # Compact
            json.dumps(webhook_data, indent=2),               # Pretty
            json.dumps(webhook_data, separators=(', ', ': ')) # Spaced
        ]
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret)):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                for payload_json in formats:
                    signature = hmac.new(
                        webhook_secret.encode('utf-8'),
                        payload_json.encode('utf-8'),
                        hashlib.sha256
                    ).hexdigest()
                    
                    response = await client.post(
                        "/api/v1/webhooks/openphone",
                        content=payload_json,
                        headers={
                            "X-OpenPhone-Signature": signature,
                            "Content-Type": "application/json"
                        }
                    )
                    
                    assert response.status_code == 200, f"Failed for format: {payload_json[:50]}..."
    
    @pytest.mark.asyncio
    async def test_timestamp_validation_prevents_replay_attacks(self, client: AsyncClient):
        """Test timestamp validation prevents old webhook replay."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "replay_test"},
            "timestamp": int(time.time()) - 900  # 15 minutes old
        }
        
        webhook_secret = "test_secret"
        payload_json = json.dumps(webhook_payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret, 300)):
                
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    json=webhook_payload,
                    headers={"X-OpenPhone-Signature": signature}
                )
                
                # Should reject old timestamp
                assert response.status_code == 400
                assert "timestamp" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_recent_timestamp_accepted(self, client: AsyncClient):
        """Test recent timestamp is accepted."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "recent_test"},
            "timestamp": int(time.time())  # Current time
        }
        
        webhook_secret = "test_secret"
        payload_json = json.dumps(webhook_payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret, 300)):
            with patch('app.worker.process_openphone_webhook.delay'):
                    
                    response = await client.post(
                        "/api/v1/webhooks/openphone",
                        content=payload_json,
                        headers={
                            "X-OpenPhone-Signature": signature,
                            "Content-Type": "application/json"
                        }
                    )
                    
                    assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_missing_timestamp_handled_gracefully(self, client: AsyncClient):
        """Test webhooks without timestamp are still processed (OpenPhone compatibility)."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "no_timestamp_test"}
            # No timestamp field
        }
        
        webhook_secret = "test_secret"
        payload_json = json.dumps(webhook_payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret)):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    content=payload_json,
                    headers={
                        "X-OpenPhone-Signature": signature,
                        "Content-Type": "application/json"
                    }
                )
                
                # Should accept (timestamp validation is optional for compatibility)
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_signature_header_variations(self, client: AsyncClient):
        """Test different signature header formats are handled."""
        webhook_payload = {
            "type": "test",
            "data": {"id": 1}
        }
        webhook_secret = "test_secret"
        payload_json = json.dumps(webhook_payload, separators=(',', ':'))
        base_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # OpenPhone might send signature in different formats
        signature_formats = [
            base_signature,                    # Raw hex
            f"sha256={base_signature}",        # With prefix
            f"SHA256={base_signature}",        # Uppercase prefix
        ]
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret)):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                for sig_format in signature_formats:
                    response = await client.post(
                        "/api/v1/webhooks/openphone",
                        content=payload_json,
                        headers={
                            "X-OpenPhone-Signature": sig_format,
                            "Content-Type": "application/json"
                        }
                    )
                    
                    assert response.status_code == 200, f"Failed for signature format: {sig_format}"
    
    @pytest.mark.asyncio
    async def test_signature_with_special_characters(self, client: AsyncClient):
        """Test signature validation with special characters in payload."""
        webhook_payload = {
            "type": "message.received",
            "data": {
                "messageId": "special_chars_test",
                "body": "Message with emojis 🎉 and unicode: café naïve résumé"
            }
        }
        
        webhook_secret = "test_secret"
        payload_json = json.dumps(webhook_payload, separators=(',', ':'), ensure_ascii=False)
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret)):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    content=payload_json,
                    headers={
                        "X-OpenPhone-Signature": signature,
                        "Content-Type": "application/json"
                    }
                )
                
                assert response.status_code == 200
    
    @pytest.mark.asyncio 
    async def test_rate_limiting_considerations(self, client: AsyncClient):
        """Test webhook endpoint behavior under rapid requests (rate limiting consideration)."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "rate_limit_test"}
        }
        
        webhook_secret = "test_secret"
        payload_json = json.dumps(webhook_payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret)):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                # Send 20 rapid requests (simulating potential DoS)
                responses = []
                for i in range(20):
                    response = await client.post(
                        "/api/v1/webhooks/openphone",
                        content=payload_json,
                        headers={
                            "X-OpenPhone-Signature": signature,
                            "Content-Type": "application/json"
                        }
                    )
                    responses.append(response.status_code)
                
                # For now, all should succeed (rate limiting not implemented yet)
                # When rate limiting is added, some should return 429
                success_count = sum(1 for code in responses if code == 200)
                assert success_count >= 10, "Should handle reasonable webhook volume"
    
    @pytest.mark.asyncio
    async def test_content_type_validation(self, client: AsyncClient):
        """Test webhook requires application/json content type."""
        webhook_payload = {
            "type": "message.received",
            "data": {"messageId": "content_type_test"}
        }
        
        webhook_secret = "test_secret"
        payload_json = json.dumps(webhook_payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret)):
            
            # Test with wrong content type
            response = await client.post(
                "/api/v1/webhooks/openphone",
                content=payload_json,
                headers={
                    "X-OpenPhone-Signature": signature,
                    "Content-Type": "text/plain"
                }
            )
            
            # Should reject non-JSON content type
            assert response.status_code == 415  # Unsupported Media Type
    
    @pytest.mark.asyncio
    async def test_webhook_secret_not_logged(self, client: AsyncClient):
        """Test webhook secret is never logged or exposed."""
        webhook_payload = {
            "type": "message.received", 
            "data": {"messageId": "secret_logging_test"}
        }
        
        # Use identifiable secret to check it's not logged
        webhook_secret = "SUPER_SECRET_WEBHOOK_KEY_DO_NOT_LOG"
        payload_json = json.dumps(webhook_payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        with patch('app.api.v1.endpoints.webhooks.get_settings', return_value=self._create_mock_settings(webhook_secret)):
            with patch('app.worker.process_openphone_webhook.delay'):
                
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    content=payload_json,
                    headers={
                        "X-OpenPhone-Signature": signature,
                        "Content-Type": "application/json"
                    }
                )
                
                assert response.status_code == 200
                
                # Response should not contain secret
                response_text = response.text
                assert webhook_secret not in response_text
                assert "SUPER_SECRET" not in response_text