"""Live monitoring endpoints — WebSocket + SSE for real-time pipeline tracking."""

import asyncio
import json
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse

from config.logging_config import get_logger
from services.event_bus import event_bus, PipelineEvent

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/live/{incident_id}")
async def websocket_live(
    websocket: WebSocket,
    incident_id: UUID,
):
    """WebSocket endpoint for real-time pipeline event streaming.
    
    Connects to the event bus for the given incident and streams
    pipeline events as JSON messages. Includes historical events
    on initial connection.
    
    Protocol:
    - Server sends: {"type": "STAGE_STARTED", "stage": "sanitizer", ...}
    - Client can send: {"type": "ping"} for keepalive
    - Connection closes when pipeline completes or client disconnects
    """
    await websocket.accept()
    
    logger.info(
        "WebSocket client connected",
        incident_id=str(incident_id),
    )
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "CONNECTED",
            "incident_id": str(incident_id),
            "message": "Connected to live pipeline monitoring",
        })
        
        # Stream events from the event bus
        async for event in event_bus.subscribe(incident_id, include_history=True):
            # Skip keepalive for WebSocket (we handle it separately)
            if event.event_type == "KEEPALIVE":
                await websocket.send_json({"type": "KEEPALIVE"})
                continue
            
            await websocket.send_json(event.to_dict())
            
            # If pipeline is done, close gracefully
            if event.event_type in (
                PipelineEvent.PIPELINE_COMPLETE,
                PipelineEvent.PIPELINE_FAILED,
            ):
                await websocket.close(1000, "Pipeline completed")
                break
    
    except WebSocketDisconnect:
        logger.info(
            "WebSocket client disconnected",
            incident_id=str(incident_id),
        )
    except Exception as e:
        logger.warning(
            "WebSocket error",
            incident_id=str(incident_id),
            error=str(e),
        )
        try:
            await websocket.close(1011, "Internal error")
        except Exception:
            pass


@router.get("/live/{incident_id}/stream")
async def sse_live(incident_id: UUID):
    """Server-Sent Events (SSE) endpoint for pipeline monitoring.
    
    Fallback for environments that don't support WebSocket.
    Streams events as text/event-stream format.
    
    Usage:
        const evtSource = new EventSource('/api/v1/live/{id}/stream');
        evtSource.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    async def event_generator():
        try:
            async for event in event_bus.subscribe(incident_id, include_history=True):
                if event.event_type == "KEEPALIVE":
                    yield ": keepalive\n\n"
                    continue
                
                data = json.dumps(event.to_dict())
                yield f"event: {event.event_type}\ndata: {data}\n\n"
                
                # Stop streaming when pipeline is done
                if event.event_type in (
                    PipelineEvent.PIPELINE_COMPLETE,
                    PipelineEvent.PIPELINE_FAILED,
                ):
                    # Send final event and close
                    yield f"event: DONE\ndata: {{}}\n\n"
                    break
        
        except asyncio.CancelledError:
            logger.info("SSE client disconnected", incident_id=str(incident_id))
        except Exception as e:
            logger.warning("SSE error", incident_id=str(incident_id), error=str(e))
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/live/{incident_id}/history")
async def get_event_history(incident_id: UUID) -> Dict[str, Any]:
    """Get historical events for an incident.
    
    Useful for getting the current state of a pipeline
    without establishing a WebSocket/SSE connection.
    """
    history = event_bus.get_history(incident_id)
    subscribers = event_bus.get_subscriber_count(incident_id)
    
    return {
        "incident_id": str(incident_id),
        "events": history,
        "event_count": len(history),
        "active_subscribers": subscribers,
    }
