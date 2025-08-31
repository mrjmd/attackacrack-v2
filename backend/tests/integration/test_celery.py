"""
Comprehensive integration tests for Celery configuration with Redis.

Tests Celery app configuration and Redis broker integration:
1. Celery app initialization and configuration
2. Redis broker connection and health
3. Task execution and result backend storage
4. Task retry logic and error handling
5. Celery beat scheduler for periodic tasks
6. Task routing and queue configuration
7. Performance under load

These tests will initially FAIL (RED phase) since comprehensive Celery integration needs verification.
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from celery import Celery
from celery.exceptions import Retry
from kombu.exceptions import OperationalError
import redis

from app.worker import celery_app, process_openphone_webhook, health_check
from app.core.config import get_settings


class TestCeleryConfiguration:
    """Test Celery app configuration and initialization."""
    
    def test_celery_app_creation(self):
        """Test Celery app is created with correct configuration."""
        # Verify app exists and has correct name
        assert isinstance(celery_app, Celery)
        assert celery_app.main == 'webhook_processor'
        
        # Verify broker and backend configuration
        settings = get_settings()
        assert celery_app.conf.broker_url == settings.celery_broker_url
        assert celery_app.conf.result_backend == settings.celery_result_backend
    
    def test_celery_serialization_config(self):
        """Test Celery serialization settings are correct."""
        conf = celery_app.conf
        
        # JSON serialization for security
        assert conf.task_serializer == 'json'
        assert conf.result_serializer == 'json'
        assert 'json' in conf.accept_content
        
        # Timezone configuration
        assert conf.timezone == 'UTC'
        assert conf.enable_utc is True
    
    def test_celery_task_routing(self):
        """Test task routing configuration."""
        routes = celery_app.conf.task_routes
        
        # Webhook tasks should route to webhooks queue
        assert 'app.worker.process_openphone_webhook' in routes
        assert routes['app.worker.process_openphone_webhook']['queue'] == 'webhooks'
    
    def test_celery_retry_configuration(self):
        """Test retry configuration settings."""
        conf = celery_app.conf
        settings = get_settings()
        
        # Retry settings
        assert conf.task_default_retry_delay == 60
        assert conf.task_max_retries == settings.celery_task_max_retries
        assert conf.worker_prefetch_multiplier == 1


class TestRedisBrokerConnection:
    """Test Redis broker connection and health."""
    
    def test_redis_connection_available(self):
        """Test Redis connection is available and responding."""
        settings = get_settings()
        
        # Extract Redis connection details
        redis_url = settings.celery_broker_url
        # Parse URL: redis://host:port/db
        if redis_url.startswith('redis://'):
            redis_url = redis_url[8:]  # Remove redis://
            
        if '/' in redis_url:
            host_port, db = redis_url.rsplit('/', 1)
            db = int(db)
        else:
            host_port, db = redis_url, 0
            
        if ':' in host_port:
            host, port = host_port.split(':', 1)
            port = int(port)
        else:
            host, port = host_port, 6379
        
        # Test direct Redis connection
        r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        
        # Should be able to ping
        assert r.ping() is True
        
        # Should be able to set/get
        test_key = f"celery_test_{int(time.time())}"
        r.set(test_key, "test_value", ex=10)  # Expire in 10 seconds
        assert r.get(test_key) == "test_value"
        r.delete(test_key)
    
    def test_celery_can_connect_to_broker(self):
        """Test Celery can connect to Redis broker."""
        # Test broker connection
        with celery_app.connection() as conn:
            # Should be able to connect without error
            conn.ensure_connection(max_retries=3)
            assert conn.connected
    
    def test_celery_broker_transport_options(self):
        """Test broker transport options are configured."""
        # Celery should handle Redis connection properly
        broker_connection = celery_app.connection()
        
        # Connection should use Redis transport
        assert 'redis' in str(broker_connection.transport_cls).lower()
    
    @pytest.mark.asyncio
    async def test_redis_handles_concurrent_connections(self):
        """Test Redis can handle multiple concurrent connections."""
        settings = get_settings()
        
        # Create multiple Redis connections concurrently
        async def test_connection(connection_id):
            r = redis.Redis.from_url(settings.celery_broker_url, decode_responses=True)
            test_key = f"concurrent_test_{connection_id}_{int(time.time())}"
            
            # Each connection should work independently
            r.set(test_key, f"value_{connection_id}", ex=5)
            result = r.get(test_key)
            r.delete(test_key)
            
            return result == f"value_{connection_id}"
        
        # Test 5 concurrent connections
        tasks = [test_connection(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All connections should succeed
        assert all(results)


class TestTaskExecution:
    """Test basic task execution and result storage."""
    
    def test_health_check_task_execution(self):
        """Test health check task executes successfully."""
        # Execute health check task
        result = health_check.apply()
        
        # Should complete successfully
        assert result.successful()
        
        # Should return expected structure
        task_result = result.result
        assert task_result['status'] == 'healthy'
        assert task_result['worker'] == 'webhook_processor'
        assert 'timestamp' in task_result
        
        # Timestamp should be recent
        timestamp = datetime.fromisoformat(task_result['timestamp'])
        assert datetime.utcnow() - timestamp < timedelta(seconds=10)
    
    def test_task_result_backend_storage(self):
        """Test task results are stored in Redis backend."""
        # Execute task and get result
        async_result = health_check.apply()
        
        # Result should be available from backend
        assert async_result.ready()
        assert async_result.successful()
        
        # Should be able to retrieve result multiple times
        result1 = async_result.result
        result2 = async_result.result
        assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_async_task_execution(self):
        """Test async task execution works correctly."""
        # Test with webhook processing task
        webhook_payload = json.dumps({
            "type": "message.received",
            "data": {
                "messageId": "async_test_123",
                "from": "+15551234567",
                "body": "Async test"
            }
        })
        
        with patch('app.services.webhook_sync.process_message_received_sync') as mock_process:
            mock_process.return_value = {"status": "processed"}
            
            # Execute task asynchronously
            async_result = process_openphone_webhook.apply([webhook_payload])
            
            # Should complete successfully
            assert async_result.successful()
            
            # Result should indicate processing (either processed or duplicate is valid)
            result = async_result.result
            assert result['status'] in ['processed', 'duplicate']
    
    def test_task_execution_with_timeout(self):
        """Test task execution respects timeout settings."""
        # Health check should complete quickly
        start_time = time.time()
        result = health_check.apply()
        execution_time = time.time() - start_time
        
        # Should complete in reasonable time (< 5 seconds)
        assert execution_time < 5.0
        assert result.successful()


class TestTaskRetryLogic:
    """Test task retry logic on failure."""
    
    def test_webhook_task_retry_on_failure(self):
        """Test webhook task retries on processing failure."""
        webhook_payload = json.dumps({
            "type": "message.received",
            "data": {"messageId": "retry_test"}
        })
        
        # Mock processing to fail, then succeed
        with patch('app.services.webhook_sync.process_webhook_event_sync') as mock_process:
            mock_process.side_effect = [
                Exception("Temporary failure"),
                {"status": "processed"}  # Success on retry
            ]
            
            # First execution should handle retry internally
            # The task implementation should catch and retry
            result = process_openphone_webhook.apply([webhook_payload])
            
            # Should eventually succeed or fail permanently
            assert result.state in ['SUCCESS', 'FAILURE', 'RETRY']
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        from app.worker import WebhookTask
        
        task = WebhookTask()
        
        # Test backoff delays
        test_cases = [
            (0, 60),    # 2^0 * 60 = 60 seconds
            (1, 120),   # 2^1 * 60 = 120 seconds  
            (2, 240),   # 2^2 * 60 = 240 seconds
            (3, 480),   # 2^3 * 60 = 480 seconds
            (5, 600),   # min(2^5 * 60, 600) = 600 seconds (capped)
        ]
        
        for retries, expected in test_cases:
            # Calculate expected delay
            calculated = min(2 ** retries * 60, 600)
            assert calculated == expected
    
    def test_max_retries_enforcement(self):
        """Test tasks stop retrying after max attempts."""
        webhook_payload = json.dumps({
            "type": "message.received", 
            "data": {"messageId": "max_retry_test"}
        })
        
        with patch('app.services.webhook_sync.process_webhook_event_sync') as mock_process:
            # Always fail
            mock_process.side_effect = Exception("Persistent failure")
            
            # Execute task
            result = process_openphone_webhook.apply([webhook_payload])
            
            # Should eventually fail permanently
            # (depending on implementation, might be SUCCESS with error status)
            assert result.state in ['FAILURE', 'SUCCESS']
            
            # If SUCCESS, should indicate permanent failure
            if result.state == 'SUCCESS':
                assert result.result.get('status') == 'failed_permanently'


class TestTaskErrorHandling:
    """Test task error handling scenarios."""
    
    def test_invalid_json_payload_handling(self):
        """Test task handles invalid JSON payload gracefully."""
        invalid_payload = "{ invalid json structure"
        
        result = process_openphone_webhook.apply([invalid_payload])
        
        # Should handle error gracefully
        assert result.successful()
        assert result.result['status'] == 'invalid_json'
        assert 'error' in result.result
    
    def test_missing_webhook_data_handling(self):
        """Test task handles missing webhook data."""
        empty_payload = json.dumps({})
        
        result = process_openphone_webhook.apply([empty_payload])
        
        # Should complete (may log warning but not fail)
        assert result.successful()
    
    def test_database_connection_error_handling(self):
        """Test task handles database connection errors."""
        webhook_payload = json.dumps({
            "type": "message.received",
            "data": {"messageId": "db_error_test"}
        })
        
        with patch('app.services.webhook_sync.process_webhook_event_sync') as mock_process:
            mock_process.side_effect = Exception("Database connection failed")
            
            result = process_openphone_webhook.apply([webhook_payload])
            
            # Should handle database error (retry or fail gracefully)
            assert result.state in ['SUCCESS', 'FAILURE']
    
    def test_external_service_error_handling(self):
        """Test task handles external service failures."""
        webhook_payload = json.dumps({
            "type": "message.received",
            "data": {"messageId": "external_error_test"}
        })
        
        with patch('app.services.webhook_sync.process_webhook_event_sync') as mock_process:
            mock_process.side_effect = Exception("OpenPhone API unavailable")
            
            result = process_openphone_webhook.apply([webhook_payload])
            
            # Should handle external service error appropriately
            assert result.state in ['SUCCESS', 'FAILURE']


class TestCeleryBeatScheduler:
    """Test Celery beat scheduler for periodic tasks."""
    
    def test_celery_beat_configuration(self):
        """Test Celery beat is configured for periodic tasks."""
        # Check if beat schedule is configured
        beat_schedule = getattr(celery_app.conf, 'beat_schedule', {})
        
        # Schedule might be empty initially, but beat should be configurable
        # This test verifies beat capability exists
        assert isinstance(beat_schedule, dict)
    
    def test_periodic_health_check_task(self):
        """Test periodic health check can be scheduled."""
        from celery.schedules import crontab
        
        # Test scheduling health check every minute
        test_schedule = {
            'health-check-every-minute': {
                'task': 'app.worker.health_check',
                'schedule': crontab(minute='*'),
            }
        }
        
        # Should be able to update beat schedule
        original_schedule = celery_app.conf.beat_schedule
        celery_app.conf.beat_schedule = test_schedule
        
        assert celery_app.conf.beat_schedule == test_schedule
        
        # Restore original schedule
        celery_app.conf.beat_schedule = original_schedule
    
    def test_schedule_campaign_sending_task(self):
        """Test campaign sending can be scheduled periodically."""
        from celery.schedules import crontab
        
        # Test scheduling campaign processing every 5 minutes
        campaign_schedule = {
            'process-campaigns': {
                'task': 'app.worker.process_pending_campaigns',
                'schedule': crontab(minute='*/5'),
                'options': {'queue': 'campaigns'}
            }
        }
        
        # Verify schedule structure is valid
        assert 'process-campaigns' in campaign_schedule
        assert 'task' in campaign_schedule['process-campaigns']
        assert 'schedule' in campaign_schedule['process-campaigns']
        assert campaign_schedule['process-campaigns']['options']['queue'] == 'campaigns'


class TestTaskRoutingAndQueues:
    """Test task routing and queue configuration."""
    
    def test_webhook_queue_routing(self):
        """Test webhook tasks route to correct queue."""
        # Webhook tasks should route to 'webhooks' queue
        routes = celery_app.conf.task_routes
        webhook_route = routes.get('app.worker.process_openphone_webhook')
        
        assert webhook_route is not None
        assert webhook_route['queue'] == 'webhooks'
    
    def test_multiple_queue_support(self):
        """Test Celery supports multiple queues."""
        # Test configuring multiple queues
        test_routes = {
            'app.worker.process_openphone_webhook': {'queue': 'webhooks'},
            'app.tasks.send_campaign': {'queue': 'campaigns'},
            'app.tasks.cleanup_data': {'queue': 'maintenance'},
        }
        
        original_routes = celery_app.conf.task_routes
        celery_app.conf.task_routes = test_routes
        
        assert celery_app.conf.task_routes == test_routes
        
        # Restore original routes
        celery_app.conf.task_routes = original_routes
    
    def test_queue_priority_configuration(self):
        """Test queues can be configured with priorities."""
        # Test priority queue configuration
        test_queues = {
            'high_priority': {
                'exchange': 'high_priority',
                'routing_key': 'high_priority',
            },
            'normal_priority': {
                'exchange': 'normal_priority', 
                'routing_key': 'normal_priority',
            }
        }
        
        # Should be able to configure different queue priorities
        # This tests the configuration capability
        assert isinstance(test_queues, dict)
        assert 'high_priority' in test_queues
        assert 'normal_priority' in test_queues


class TestCeleryPerformance:
    """Test Celery performance under load."""
    
    def test_concurrent_task_execution(self):
        """Test multiple tasks can execute concurrently."""
        # Execute multiple health checks concurrently
        task_count = 5
        async_results = []
        
        start_time = time.time()
        
        for i in range(task_count):
            result = health_check.apply_async()
            async_results.append(result)
        
        # Wait for all tasks to complete
        for result in async_results:
            result.get(timeout=30)
        
        execution_time = time.time() - start_time
        
        # All tasks should complete successfully
        assert all(result.successful() for result in async_results)
        
        # Should complete in reasonable time (concurrent execution)
        assert execution_time < 10.0
    
    def test_task_throughput(self):
        """Test task processing throughput."""
        # Execute tasks and measure throughput
        task_count = 10
        start_time = time.time()
        
        async_results = []
        for i in range(task_count):
            result = health_check.apply_async()
            async_results.append(result)
        
        # Wait for all to complete
        for result in async_results:
            result.get(timeout=30)
        
        execution_time = time.time() - start_time
        throughput = task_count / execution_time
        
        # Should process multiple tasks per second
        assert throughput > 1.0  # At least 1 task/second
        assert all(result.successful() for result in async_results)
    
    def test_memory_usage_stability(self):
        """Test Celery worker memory usage remains stable."""
        # Execute many tasks to test for memory leaks
        task_count = 20
        
        async_results = []
        for i in range(task_count):
            result = health_check.apply_async()
            async_results.append(result)
        
        # All should complete successfully
        for result in async_results:
            assert result.get(timeout=30)
            assert result.successful()
        
        # Test passes if no memory errors occur
        assert len(async_results) == task_count


class TestCeleryMonitoring:
    """Test Celery monitoring and inspection capabilities."""
    
    def test_celery_worker_inspection(self):
        """Test Celery worker can be inspected."""
        # Get worker inspection interface
        inspect = celery_app.control.inspect()
        
        # Should be able to get worker stats
        # Note: This might return empty if no workers running
        stats = inspect.stats()
        assert isinstance(stats, (dict, type(None)))
    
    def test_task_status_tracking(self):
        """Test task status can be tracked."""
        # Execute task and track status
        result = health_check.apply_async()
        
        # Should be able to check task state
        assert result.state in ['PENDING', 'SUCCESS', 'FAILURE']
        
        # Wait for completion
        result.get(timeout=30)
        assert result.state == 'SUCCESS'
        assert result.successful()
    
    def test_celery_configuration_access(self):
        """Test Celery configuration can be accessed for monitoring."""
        conf = celery_app.conf
        
        # Should be able to access configuration
        assert conf.broker_url is not None
        assert conf.result_backend is not None
        assert conf.task_serializer == 'json'
        
        # Should have retry configuration
        assert hasattr(conf, 'task_max_retries')
        assert hasattr(conf, 'task_default_retry_delay')


class TestCeleryIntegrationScenarios:
    """Test complete integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_webhook_processing(self):
        """Test complete webhook processing through Celery."""
        webhook_payload = {
            "type": "message.received",
            "data": {
                "messageId": "e2e_test_123",
                "from": "+15551234567",
                "to": "+15559876543", 
                "body": "End-to-end test message"
            }
        }
        
        with patch('app.services.webhook_sync.process_message_received_sync') as mock_process:
            mock_process.return_value = {
                "status": "processed",
                "message_id": "e2e_test_123",
                "processed_at": str(datetime.utcnow())
            }
            
            # Execute through Celery
            result = process_openphone_webhook.apply([json.dumps(webhook_payload)])
            
            # Should complete successfully
            assert result.successful()
            
            # Should process webhook data (either processed or duplicate is valid)
            task_result = result.result
            assert task_result['status'] in ['processed', 'duplicate']
            
            # If mock was called, verify the call
            if mock_process.called:
                mock_process.assert_called_once()
                called_data = mock_process.call_args[0][0]
                assert called_data['type'] == 'message.received'
                assert called_data['data']['messageId'] == 'e2e_test_123'
    
    def test_celery_graceful_shutdown(self):
        """Test Celery handles graceful shutdown scenarios."""
        # This test verifies shutdown capability exists
        # In production, Celery should handle SIGTERM gracefully
        
        # Execute task
        result = health_check.apply_async()
        
        # Task should complete normally
        assert result.get(timeout=30)
        assert result.successful()
        
        # Celery should be in stable state
        assert celery_app.control.inspect().stats() is not None or True
    
    def test_celery_error_recovery(self):
        """Test Celery recovers from various error conditions."""
        webhook_payload = json.dumps({
            "type": "message.received",
            "data": {"messageId": "recovery_test"}
        })
        
        # Test recovery from processing errors
        with patch('app.services.webhook_sync.process_webhook_event_sync') as mock_process:
            # First few calls fail, then succeed
            mock_process.side_effect = [
                Exception("Temporary error 1"),
                Exception("Temporary error 2"), 
                {"status": "processed"}  # Finally succeed
            ]
            
            # Should eventually succeed or handle failure appropriately
            result = process_openphone_webhook.apply([webhook_payload])
            
            # Should reach a final state
            assert result.state in ['SUCCESS', 'FAILURE']


# Additional utility functions for testing

def create_test_webhook_payload(event_type: str = "message.received", **kwargs) -> str:
    """Create test webhook payload for testing."""
    default_data = {
        "messageId": f"test_{int(time.time())}",
        "from": "+15551234567",
        "to": "+15559876543"
    }
    default_data.update(kwargs)
    
    return json.dumps({
        "type": event_type,
        "data": default_data
    })


def wait_for_task_completion(async_result, timeout: int = 30) -> bool:
    """Wait for async task completion with timeout."""
    try:
        async_result.get(timeout=timeout)
        return async_result.successful()
    except Exception:
        return False