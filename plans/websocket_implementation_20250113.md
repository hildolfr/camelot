# WebSocket Implementation Plan
Date: 2025-01-13
Status: PROPOSED

## Overview
Replace the current polling-based game state updates with WebSocket connections for real-time, bidirectional communication.

## Current Issues with Polling
1. **Inefficient** - Constant HTTP requests even when nothing changes
2. **Delayed Updates** - Up to 2-second delay between actions
3. **Race Conditions** - Multiple clients polling can still cause timing issues
4. **Server Load** - Each poll is a full HTTP request/response cycle
5. **Battery Drain** - Mobile devices constantly making requests

## Benefits of WebSocket Implementation
1. **Real-time Updates** - Instant state propagation to all clients
2. **Reduced Latency** - No polling interval delays
3. **Lower Bandwidth** - Only send deltas, not full state
4. **Better Scalability** - Fewer connections and requests
5. **Enables New Features** - Chat, spectators, notifications

## Architecture Design

### Backend Changes

#### 1. WebSocket Manager
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # game_id -> {player_id: websocket}
    
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][player_id] = websocket
    
    async def disconnect(self, game_id: str, player_id: str):
        if game_id in self.active_connections:
            self.active_connections[game_id].pop(player_id, None)
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id].values():
                await connection.send_json(message)
```

#### 2. WebSocket Endpoints
```python
@router.websocket("/ws/game/{game_id}/{player_id}")
async def game_websocket(websocket: WebSocket, game_id: str, player_id: str):
    await manager.connect(websocket, game_id, player_id)
    try:
        while True:
            # Receive actions from client
            data = await websocket.receive_json()
            await process_websocket_action(game_id, player_id, data)
    except WebSocketDisconnect:
        await manager.disconnect(game_id, player_id)
```

#### 3. Game State Broadcasting
- After each action, broadcast state changes to all connected clients
- Send only deltas when possible (e.g., "player X folded" vs entire state)
- Include animation triggers in broadcasts

### Frontend Changes

#### 1. WebSocket Connection Management
```javascript
class GameWebSocket {
    constructor(gameId, playerId) {
        this.gameId = gameId;
        this.playerId = playerId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.messageQueue = [];
    }
    
    connect() {
        const wsUrl = `ws://localhost:8000/ws/game/${this.gameId}/${this.playerId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.flushMessageQueue();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.reconnect();
        };
    }
    
    send(message) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            this.messageQueue.push(message);
        }
    }
}
```

#### 2. Replace Polling with WebSocket Events
- Remove all `setInterval` polling
- Update state based on WebSocket messages
- Keep HTTP endpoints as fallback

## Implementation Steps

### Phase 1: Basic WebSocket Infrastructure
1. Add WebSocket support to FastAPI
2. Create ConnectionManager class
3. Implement basic connect/disconnect handling
4. Add WebSocket endpoint for games

### Phase 2: Game Integration
1. Modify game actions to broadcast via WebSocket
2. Update frontend to use WebSocket for actions
3. Implement state synchronization protocol
4. Add connection recovery logic

### Phase 3: Optimization
1. Implement delta updates (send only changes)
2. Add message compression
3. Implement heartbeat/ping-pong
4. Add connection pooling

### Phase 4: Advanced Features
1. Spectator mode (read-only connections)
2. Game chat functionality
3. Real-time notifications
4. Connection status indicators

## Message Protocol

### Client to Server
```json
{
    "type": "action",
    "action": "fold|check|call|raise|all_in",
    "amount": 100,
    "request_id": "uuid"
}
```

### Server to Client
```json
{
    "type": "state_update|animation|notification",
    "data": {
        // Partial or full state update
    },
    "timestamp": 1234567890
}
```

## Testing Strategy
1. Connection stability tests
2. Concurrent connection tests
3. Reconnection scenarios
4. Message ordering guarantees
5. Performance benchmarks

## Rollback Plan
- Keep HTTP endpoints active
- Add feature flag for WebSocket mode
- Gradual rollout to users
- Monitor connection metrics

## Success Metrics
1. Reduced server load (fewer HTTP requests)
2. Lower action latency (<100ms vs 2000ms)
3. Improved user satisfaction
4. Stable connections (>99% uptime)
5. Successful reconnection rate (>95%)

## Timeline
- Phase 1: 3-4 hours
- Phase 2: 4-5 hours  
- Phase 3: 2-3 hours
- Phase 4: 3-4 hours

Total: 12-16 hours of implementation