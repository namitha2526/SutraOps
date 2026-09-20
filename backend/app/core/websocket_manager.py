from typing import Dict, List
from fastapi import WebSocket
from app.core.logging import StructuredLogger

class ConnectionManager:
    """
    Manages active WebSocket connections mapped strictly by tenant (organization_id)
    to guarantee isolation.
    """
    def __init__(self):
        # Maps organization_id_str -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, organization_id: str):
        await websocket.accept()
        if organization_id not in self.active_connections:
            self.active_connections[organization_id] = []
        self.active_connections[organization_id].append(websocket)
        StructuredLogger.info(
            f"WebSocket client registered on tenant tunnel: {organization_id}. "
            f"Total active listeners in tenant: {len(self.active_connections[organization_id])}"
        )

    def disconnect(self, websocket: WebSocket, organization_id: str):
        if organization_id in self.active_connections:
            if websocket in self.active_connections[organization_id]:
                self.active_connections[organization_id].remove(websocket)
                StructuredLogger.info(
                    f"WebSocket client disconnected from tenant tunnel: {organization_id}. "
                    f"Remaining listeners: {len(self.active_connections[organization_id])}"
                )
            if not self.active_connections[organization_id]:
                del self.active_connections[organization_id]

    async def broadcast_to_tenant(self, organization_id: str, message: dict):
        """
        Sends a JSON payload broadcast to all connected WebSocket clients within the organization context scope.
        """
        org_id_str = str(organization_id)
        connections = self.active_connections.get(org_id_str, [])
        if not connections:
            return

        StructuredLogger.info(
            f"Broadcasting real-time event to tenant {org_id_str} (Connections: {len(connections)})"
        )
        
        # Collect failed sockets to clean up
        failed_sockets = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                StructuredLogger.warning(f"Failed to transmit websocket message, cleaning up socket: {str(e)}")
                failed_sockets.append(connection)

        # Cleanup failed connections
        for stale in failed_sockets:
            self.disconnect(stale, org_id_str)


# Global singleton instance
ws_manager = ConnectionManager()
