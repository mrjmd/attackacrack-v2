"""
Celery worker for asynchronous webhook processing.

Handles queued webhook events with retry logic and dead letter queue.
"""

import json
import logging
from typing import Dict, Any

from celery import Celery, Task
from celery.exceptions import Retry

from app.core.config import get_settings
from app.services.webhook import process_webhook_event, handle_failed_webhook

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create Celery app
celery_app = Celery(
    'webhook_processor',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.worker']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'app.worker.process_openphone_webhook': {'queue': 'webhooks'},
    },
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=settings.celery_task_max_retries,
    worker_prefetch_multiplier=1,  # Disable prefetching for better load distribution
)


class WebhookTask(Task):
    """Base task class for webhook processing with custom retry logic."""
    
    def retry_with_exponential_backoff(self, exc, max_retries=None):
        """Retry with exponential backoff delay."""
        if max_retries is None:
            max_retries = settings.celery_task_max_retries
        
        if self.request.retries >= max_retries:
            # Max retries exceeded - don't retry anymore
            raise exc
        
        # Calculate exponential backoff: min(2^retries * 60, 600) seconds
        countdown = min(2 ** self.request.retries * 60, 600)
        
        logger.warning(
            f"Retrying webhook processing (attempt {self.request.retries + 1}/{max_retries + 1}) "
            f"in {countdown}s: {str(exc)}"
        )
        
        raise self.retry(countdown=countdown, exc=exc)


@celery_app.task(bind=True, base=WebhookTask)
def process_openphone_webhook(self, webhook_payload: str) -> Dict[str, Any]:
    """
    Process OpenPhone webhook event asynchronously.
    
    Args:
        webhook_payload: JSON string of webhook payload
        
    Returns:
        Dict: Processing result with status and details
    """
    try:
        # Parse webhook payload
        try:
            webhook_data = json.loads(webhook_payload)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {str(e)}")
            return {
                'status': 'invalid_json',
                'error': str(e)
            }
        
        event_type = webhook_data.get('type', 'unknown')
        
        logger.info(f"Processing webhook event: {event_type}")
        
        # Process the webhook event
        import asyncio
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an event loop (like during testing)
                # Use asyncio.run_coroutine_threadsafe or await directly if we have an async task
                import concurrent.futures
                import threading
                
                # Create a new event loop in a separate thread
                def run_in_new_loop():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(process_webhook_event(webhook_data))
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_new_loop)
                    result = future.result()
            else:
                result = asyncio.run(process_webhook_event(webhook_data))
        except RuntimeError:
            # Fallback for edge cases
            result = asyncio.run(process_webhook_event(webhook_data))
        
        # Check if processing was successful
        if result.get('status') in ['processed', 'duplicate', 'ignored']:
            logger.info(f"Successfully processed webhook: {event_type} - {result['status']}")
            return result
        else:
            # Processing failed - this will trigger retry
            error_msg = result.get('error', 'Unknown processing error')
            raise Exception(f"Webhook processing failed: {error_msg}")
    
    except Exception as exc:
        logger.error(f"Error processing webhook: {str(exc)}")
        
        # Check if we've exceeded max retries
        if self.request.retries >= settings.celery_task_max_retries:
            logger.error(f"Max retries exceeded for webhook processing: {str(exc)}")
            
            # Send to dead letter queue
            try:
                webhook_data = json.loads(webhook_payload)
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Use thread pool for async operation
                        import concurrent.futures
                        
                        def run_handle_failed():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(handle_failed_webhook(webhook_data, str(exc)))
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_handle_failed)
                            future.result()
                    else:
                        asyncio.run(handle_failed_webhook(webhook_data, str(exc)))
                except RuntimeError:
                    asyncio.run(handle_failed_webhook(webhook_data, str(exc)))
            except Exception as dead_letter_exc:
                logger.error(f"Failed to handle dead letter webhook: {str(dead_letter_exc)}")
            
            return {
                'status': 'failed_permanently',
                'error': str(exc),
                'retries': self.request.retries
            }
        
        # Retry with exponential backoff
        self.retry_with_exponential_backoff(exc)


@celery_app.task
def health_check() -> Dict[str, str]:
    """
    Health check task to verify Celery worker is functioning.
    
    Returns:
        Dict: Health status
    """
    from datetime import datetime
    return {
        'status': 'healthy',
        'worker': 'webhook_processor',
        'timestamp': str(datetime.utcnow())
    }


# Make tasks available for import
__all__ = ['process_openphone_webhook', 'health_check', 'celery_app']