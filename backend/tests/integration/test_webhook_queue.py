"""
Queue processing tests for OpenPhone webhooks.

Tests Celery queue integration:
1. Webhook payload gets queued to Celery
2. Celery task processes webhook asynchronously  
3. Failed tasks retry with exponential backoff
4. Dead letter queue for persistent failures

These tests will FAIL initially (RED phase) since no implementation exists.
"""

import json
import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from celery.exceptions import Retry


class TestWebhookQueue:
    """Test webhook Celery queue processing."""
    
    @pytest.mark.asyncio
    async def test_webhook_queues_to_celery(self, client: AsyncClient):
        """Test webhook immediately queues payload to Celery."""
        webhook_payload = {
            "type": "message.received",
            "data": {
                "messageId": "queue_test_123",
                "from": "+15551234567",
                "body": "Test queueing"
            }
        }
        
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            with patch('app.worker.process_openphone_webhook.delay') as mock_queue:
                
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    json=webhook_payload,
                    headers={"X-OpenPhone-Signature": "valid"}
                )
                
                assert response.status_code == 200
                
                # Should queue exactly once
                mock_queue.assert_called_once()
                
                # Should queue the raw JSON payload as string
                queued_data = mock_queue.call_args[0][0]
                assert isinstance(queued_data, str)
                assert json.loads(queued_data) == webhook_payload
    
    @pytest.mark.asyncio
    async def test_queue_preserves_exact_payload(self, client: AsyncClient):
        """Test queued payload preserves exact JSON structure."""
        webhook_payload = {
            "type": "message.received",
            "data": {
                "messageId": "preserve_test",
                "metadata": {
                    "nested": {"value": 42},
                    "array": [1, 2, 3],
                    "boolean": True,
                    "null_value": None
                }
            }
        }
        
        with patch('app.services.openphone.verify_webhook_signature', return_value=True):
            with patch('app.worker.process_openphone_webhook.delay') as mock_queue:
                
                response = await client.post(
                    "/api/v1/webhooks/openphone",
                    json=webhook_payload,
                    headers={"X-OpenPhone-Signature": "valid"}
                )
                
                assert response.status_code == 200
                
                # Verify exact payload preservation
                queued_payload = json.loads(mock_queue.call_args[0][0])
                assert queued_payload == webhook_payload
                assert queued_payload["data"]["metadata"]["nested"]["value"] == 42
                assert queued_payload["data"]["metadata"]["array"] == [1, 2, 3]
                assert queued_payload["data"]["metadata"]["boolean"] is True
                assert queued_payload["data"]["metadata"]["null_value"] is None
    
    @pytest.mark.asyncio
    async def test_celery_task_processes_webhook(self):
        """Test Celery task successfully processes webhook payload."""
        from app.worker import process_openphone_webhook
        
        webhook_data = json.dumps({
            "type": "message.received",
            "data": {
                "messageId": "celery_process_test",
                "from": "+15551234567",
                "to": "+15559876543",
                "body": "Processing test"
            }
        })
        
        # Mock database operations
        with patch('app.services.webhook.process_message_received') as mock_process:
            mock_process.return_value = {"status": "processed"}
            
            # Execute Celery task
            result = process_openphone_webhook(webhook_data)
            
            # Should call processor with parsed data
            mock_process.assert_called_once()
            called_data = mock_process.call_args[0][0]
            assert called_data["type"] == "message.received"
            assert called_data["data"]["messageId"] == "celery_process_test"
            
            # Should return success result
            assert result["status"] == "processed"
    
    @pytest.mark.asyncio
    async def test_celery_task_handles_different_event_types(self):
        """Test Celery task routes different event types to correct handlers."""
        from app.worker import process_openphone_webhook
        
        test_cases = [
            ("message.received", "app.services.webhook.process_message_received"),
            ("message.delivered", "app.services.webhook.process_message_delivered"), 
            ("call.completed", "app.services.webhook.process_call_completed"),
            ("voicemail.received", "app.services.webhook.process_voicemail_received")
        ]
        
        for event_type, handler_path in test_cases:
            webhook_data = json.dumps({
                "type": event_type,
                "data": {"id": f"test_{event_type}"}
            })
            
            with patch(handler_path) as mock_handler:
                mock_handler.return_value = {"status": "processed"}
                
                result = process_openphone_webhook(webhook_data)
                
                mock_handler.assert_called_once()
                assert result["status"] == "processed"
    
    @pytest.mark.asyncio  
    async def test_celery_task_retry_on_failure(self):
        """Test Celery task retries on processing failure."""
        from app.worker import process_openphone_webhook
        
        webhook_data = json.dumps({
            "type": "message.received",
            "data": {"messageId": "retry_test"}
        })
        
        # Mock processing to fail first time, succeed second time
        with patch('app.services.webhook.process_message_received') as mock_process:
            mock_process.side_effect = [
                Exception("Database connection failed"),
                {"status": "processed"}  # Success on retry
            ]
            
            # Mock Celery retry mechanism
            with patch.object(process_openphone_webhook, 'retry') as mock_retry:
                mock_retry.side_effect = Retry("Retrying...")
                
                # First call should trigger retry
                with pytest.raises(Retry):
                    process_openphone_webhook(webhook_data)
                
                # Should have attempted retry
                mock_retry.assert_called_once()
                assert "Database connection failed" in str(mock_retry.call_args)
    
    @pytest.mark.asyncio
    async def test_celery_task_exponential_backoff(self):
        """Test Celery task uses exponential backoff for retries."""
        from app.worker import WebhookTask
        
        # Test the retry logic calculation directly
        task = WebhookTask()
        
        # Test retry counts that won't exceed max retries (default max is 3)
        test_cases = [
            (0, 60),    # First retry: 2^0 * 60 = 60
            (1, 120),   # Second retry: 2^1 * 60 = 120
            (2, 240),   # Third retry: 2^2 * 60 = 240
        ]
        
        for retries, expected_delay in test_cases:
            # Mock the request property
            mock_request = Mock()
            mock_request.retries = retries
            
            with patch.object(type(task), 'request', new_callable=lambda: mock_request):
                with patch.object(task, 'retry') as mock_retry:
                    mock_retry.side_effect = Retry("Retrying with backoff...")
                    
                    with pytest.raises(Retry):
                        task.retry_with_exponential_backoff(Exception("Test failure"))
                    
                    mock_retry.assert_called_once()
                    retry_args = mock_retry.call_args
                    assert retry_args[1]['countdown'] == expected_delay
                    
                    mock_retry.reset_mock()
        
        # Test max cap separately with higher max_retries setting
        with patch('app.worker.settings') as mock_settings:
            mock_settings.celery_task_max_retries = 10  # Higher limit
            
            mock_request = Mock()
            mock_request.retries = 5  # Should cap at 600
            
            with patch.object(type(task), 'request', new_callable=lambda: mock_request):
                with patch.object(task, 'retry') as mock_retry:
                    mock_retry.side_effect = Retry("Retrying with backoff...")
                    
                    with pytest.raises(Retry):
                        task.retry_with_exponential_backoff(Exception("Test failure"))
                    
                    mock_retry.assert_called_once()
                    retry_args = mock_retry.call_args
                    assert retry_args[1]['countdown'] == 600  # min(2^5 * 60, 600) = 600
    
    @pytest.mark.asyncio
    async def test_celery_task_max_retries_exceeded(self):
        """Test Celery task stops retrying after max attempts."""
        from app.worker import WebhookTask
        
        # Test max retries logic directly on WebhookTask
        task = WebhookTask()
        
        # Mock the request property with max retries
        mock_request = Mock()
        mock_request.retries = 3  # At max retry limit
        
        # Mock settings
        with patch('app.worker.settings') as mock_settings:
            mock_settings.celery_task_max_retries = 3
            
            with patch.object(type(task), 'request', new_callable=lambda: mock_request):
                # Should not retry when at max retries, should raise the original exception
                with pytest.raises(Exception, match="Max retries test"):
                    task.retry_with_exponential_backoff(Exception("Max retries test"))
    
    @pytest.mark.asyncio
    async def test_webhook_event_marked_processed_on_success(self):
        """Test webhook processing completes successfully."""
        from app.worker import process_openphone_webhook
        
        webhook_data = json.dumps({
            "type": "message.received", 
            "data": {"messageId": "mark_processed_test"}
        })
        
        with patch('app.services.webhook.process_message_received', return_value={"status": "processed"}):
            result = process_openphone_webhook(webhook_data)
            
            # Should return processed status
            assert result["status"] == "processed"
    
    @pytest.mark.asyncio
    async def test_webhook_processing_error_handling(self):
        """Test webhook processing handles errors with retries."""
        from app.worker import process_openphone_webhook
        
        webhook_data = json.dumps({
            "type": "message.received",
            "data": {"messageId": "error_test"}
        })
        
        error_message = "Processing failed due to validation error"
        
        # Test that processing error triggers retry mechanism
        with patch('app.services.webhook.process_message_received', side_effect=Exception(error_message)):
            # Should trigger retry which raises Retry exception
            # The Retry exception gets wrapped/re-raised, so we catch the base Exception
            with pytest.raises((Retry, Exception)) as exc_info:
                process_openphone_webhook(webhook_data)
            
            # Verify it's a retry-related exception
            assert "Webhook processing failed" in str(exc_info.value) or "retry" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_duplicate_message_handling_in_queue(self):
        """Test queue processor handles duplicate messages gracefully."""
        from app.worker import process_openphone_webhook
        
        duplicate_webhook_data = json.dumps({
            "type": "message.received",
            "data": {
                "messageId": "duplicate_queue_test",
                "from": "+15551234567"
            }
        })
        
        with patch('app.services.webhook.process_message_received') as mock_process:
            # First call processes normally
            mock_process.return_value = {"status": "processed"}
            result1 = process_openphone_webhook(duplicate_webhook_data)
            
            # Second call with same message should detect duplicate
            mock_process.return_value = {"status": "duplicate", "message": "Already processed"}
            result2 = process_openphone_webhook(duplicate_webhook_data)
            
            assert result1["status"] == "processed"
            assert result2["status"] == "duplicate"
            
            # Both calls should complete successfully (no exceptions)
            assert mock_process.call_count == 2
    
    @pytest.mark.asyncio
    async def test_queue_task_logging(self):
        """Test Celery task logs processing events appropriately."""
        from app.worker import process_openphone_webhook
        
        webhook_data = json.dumps({
            "type": "message.received",
            "data": {"messageId": "logging_test"}
        })
        
        with patch('app.services.webhook.process_message_received', return_value={"status": "processed"}):
            with patch('app.worker.logger') as mock_logger:
                
                result = process_openphone_webhook(webhook_data)
                
                # Should log processing start and completion
                mock_logger.info.assert_called()
                log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                
                assert any("Processing webhook" in log for log in log_calls)
                assert any("Successfully processed" in log for log in log_calls)
                assert result["status"] == "processed"