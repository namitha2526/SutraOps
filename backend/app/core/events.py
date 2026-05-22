import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID
from app.core.database import SessionLocal
from app.core.logging import StructuredLogger, correlation_id_ctx
from app.models.system import DeadLetterLog, Notification


class Event:
    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        organization_id: UUID,
        correlation_id: Optional[str] = None
    ):
        self.event_type = event_type
        self.payload = payload
        self.organization_id = organization_id
        self.correlation_id = correlation_id or correlation_id_ctx.get()
        self.timestamp = time.time()


class EventBus:
    """
    Asynchronous Internal Event Bus implementing publisher-subscriber pattern,
    exponential backoff failures recovery, and persistent Dead-Letter Queue logs.
    """
    _subscribers: Dict[str, List[Callable[[Event], Any]]] = {}

    @classmethod
    def subscribe(cls, event_type: str, callback: Callable[[Event], Any]):
        """
        Registers an event listener callback for a specific event channel.
        """
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(callback)
        StructuredLogger.info(f"Subscribed callback to event type channel: {event_type}")

    @classmethod
    async def publish(cls, event: Event):
        """
        Publishes an event to all active channel subscribers asynchronously in the background.
        """
        subscribers = cls._subscribers.get(event.event_type, [])
        if not subscribers:
            StructuredLogger.info(f"Published event '{event.event_type}' has no registered subscribers.")
            return

        StructuredLogger.info(
            f"Event Published: '{event.event_type}' (Subscribers: {len(subscribers)})",
            event_type=event.event_type,
            correlation_id=event.correlation_id,
            organization_id=str(event.organization_id)
        )

        for callback in subscribers:
            # Dispatch each subscriber as an independent background task
            asyncio.create_task(cls._execute_subscriber_with_retry(callback, event))

    @classmethod
    async def _execute_subscriber_with_retry(cls, callback: Callable[[Event], Any], event: Event):
        """
        Executes a subscriber callback with exponential backoff retry and DLQ persistence.
        """
        max_retries = 3
        backoff = 1.0  # Initial delay of 1 second

        for attempt in range(1, max_retries + 1):
            try:
                # Set correlation ID context for logging consistency within worker thread
                correlation_id_ctx.set(event.correlation_id or "")
                
                # Check if callback is a coroutine or normal function
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
                
                # Successful execution - exit retry loop
                return
            except Exception as e:
                StructuredLogger.warning(
                    f"Event execution failed: callback '{callback.__name__}' on event '{event.event_type}'. "
                    f"Attempt {attempt}/{max_retries}. Error: {str(e)}",
                    attempt=attempt,
                    error=str(e)
                )
                
                if attempt < max_retries:
                    # Exponential backoff delay (doubling delay)
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                else:
                    # All retries failed. Persist to Dead-Letter Log (DLQ)
                    cls._persist_to_dlq(event, callback.__name__, str(e))

    @classmethod
    def _persist_to_dlq(cls, event: Event, handler_name: str, error_msg: str):
        """
        Saves permanently failed events into the database DLQ table for diagnostics.
        """
        StructuredLogger.error(
            f"DLQ TRIGGERED: Event '{event.event_type}' permanently failed. Saved to DLQ.",
            handler=handler_name,
            error=error_msg
        )
        
        db = SessionLocal()
        try:
            dlq_log = DeadLetterLog(
                organization_id=event.organization_id,
                event_type=event.event_type,
                payload=event.payload,
                error_message=f"Handler '{handler_name}' failed permanently. Reason: {error_msg}",
                retry_count=3,
                resolved=False
            )
            db.add(dlq_log)
            db.commit()
        except Exception as e:
            StructuredLogger.error(f"Failed writing event to DLQ table! Error: {str(e)}")
        finally:
            db.close()
