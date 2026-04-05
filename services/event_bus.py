"""In-memory pub/sub event bus for real-time pipeline monitoring.

Provides live event streaming from the orchestrator to connected
WebSocket/SSE clients. Each incident gets its own event channel.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from uuid import UUID

from config.logging_config import get_logger

logger = get_logger(__name__)


class PipelineEvent:
    """A single pipeline event."""
    
    # Event types
    STAGE_STARTED = "STAGE_STARTED"
    STAGE_COMPLETED = "STAGE_COMPLETED"
    STAGE_FAILED = "STAGE_FAILED"
    LOG_LINE = "LOG_LINE"
    PIPELINE_COMPLETE = "PIPELINE_COMPLETE"
    PIPELINE_FAILED = "PIPELINE_FAILED"
    
    def __init__(
        self,
        event_type: str,
        stage: str,
        detail: str,
        progress_pct: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_type = event_type
        self.stage = stage
        self.detail = detail
        self.progress_pct = progress_pct
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON transmission."""
        return {
            "type": self.event_type,
            "stage": self.stage,
            "detail": self.detail,
            "progress_pct": self.progress_pct,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())


class EventBus:
    """In-memory event bus for pipeline monitoring.
    
    Manages per-incident event channels using asyncio Queues.
    Multiple subscribers can listen to the same incident.
    
    Usage (Publisher - in Orchestrator):
        event_bus.publish(incident_id, PipelineEvent(
            event_type=PipelineEvent.STAGE_STARTED,
            stage="sanitizer",
            detail="Scanning for secrets...",
            progress_pct=10,
        ))
    
    Usage (Subscriber - in WebSocket handler):
        async for event in event_bus.subscribe(incident_id):
            await websocket.send_json(event.to_dict())
    """
    
    def __init__(self):
        # Map: incident_id -> list of subscriber queues
        self._channels: Dict[str, List[asyncio.Queue]] = {}
        # Track recent events per incident for late-joining subscribers
        self._history: Dict[str, List[PipelineEvent]] = {}
        self._max_history = 100
        self._lock = asyncio.Lock()
    
    async def publish(
        self,
        incident_id: UUID,
        event: PipelineEvent,
    ) -> None:
        """Publish an event to all subscribers of an incident.
        
        Args:
            incident_id: The incident to publish to
            event: The pipeline event
        """
        key = str(incident_id)
        
        # Store in history
        if key not in self._history:
            self._history[key] = []
        self._history[key].append(event)
        if len(self._history[key]) > self._max_history:
            self._history[key] = self._history[key][-self._max_history:]
        
        # Broadcast to all subscriber queues
        async with self._lock:
            queues = self._channels.get(key, [])
            dead_queues = []
            
            for queue in queues:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # Drop oldest event if queue is full
                    try:
                        queue.get_nowait()
                        queue.put_nowait(event)
                    except (asyncio.QueueEmpty, asyncio.QueueFull):
                        dead_queues.append(queue)
            
            # Remove dead queues
            for dq in dead_queues:
                if dq in queues:
                    queues.remove(dq)
    
    async def subscribe(
        self,
        incident_id: UUID,
        include_history: bool = True,
    ) -> AsyncGenerator[PipelineEvent, None]:
        """Subscribe to events for an incident.
        
        Yields events as they arrive. Includes historical events
        first if include_history is True.
        
        Args:
            incident_id: The incident to subscribe to
            include_history: Whether to replay historical events
            
        Yields:
            PipelineEvent objects as they arrive
        """
        key = str(incident_id)
        queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        
        # Register subscriber
        async with self._lock:
            if key not in self._channels:
                self._channels[key] = []
            self._channels[key].append(queue)
        
        try:
            # Replay history first
            if include_history and key in self._history:
                for event in self._history[key]:
                    yield event
            
            # Stream live events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                    
                    # Stop if pipeline is complete
                    if event.event_type in (
                        PipelineEvent.PIPELINE_COMPLETE,
                        PipelineEvent.PIPELINE_FAILED,
                    ):
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield PipelineEvent(
                        event_type="KEEPALIVE",
                        stage="",
                        detail="keepalive",
                        progress_pct=-1,
                    )
        
        finally:
            # Unregister subscriber
            async with self._lock:
                if key in self._channels and queue in self._channels[key]:
                    self._channels[key].remove(queue)
                # Cleanup empty channels
                if key in self._channels and not self._channels[key]:
                    del self._channels[key]
    
    def get_history(self, incident_id: UUID) -> List[Dict[str, Any]]:
        """Get event history for an incident.
        
        Args:
            incident_id: The incident ID
            
        Returns:
            List of serialized events
        """
        key = str(incident_id)
        events = self._history.get(key, [])
        return [e.to_dict() for e in events]
    
    def get_subscriber_count(self, incident_id: UUID) -> int:
        """Get number of active subscribers for an incident."""
        key = str(incident_id)
        return len(self._channels.get(key, []))
    
    async def cleanup_incident(self, incident_id: UUID) -> None:
        """Clean up all data for a completed incident.
        
        Called after an incident is fully processed and all
        subscribers have disconnected.
        """
        key = str(incident_id)
        async with self._lock:
            self._channels.pop(key, None)
        # Keep history for a while (late-joining clients)
        # It will be garbage-collected on restart


# Global singleton event bus
event_bus = EventBus()
