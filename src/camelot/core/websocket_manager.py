"""WebSocket connection management for real-time game updates"""

import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PlayerConnection:
    """Represents a player's WebSocket connection"""
    websocket: WebSocket
    player_id: str
    game_id: str
    connected_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    is_spectator: bool = False
    
    async def send_json(self, data: Dict[str, Any]) -> bool:
        """Send JSON data to the client, return True if successful"""
        try:
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Error sending to {self.player_id}: {e}")
            return False


class GameRoom:
    """Manages WebSocket connections for a single game"""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.connections: Dict[str, PlayerConnection] = {}
        self.created_at = time.time()
        self.last_activity = time.time()
        self._lock = asyncio.Lock()
        
    async def add_connection(self, player_id: str, websocket: WebSocket, is_spectator: bool = False) -> PlayerConnection:
        """Add a player connection to the room"""
        async with self._lock:
            # Close existing connection if any
            if player_id in self.connections:
                old_conn = self.connections[player_id]
                try:
                    await old_conn.websocket.close()
                except:
                    pass
                logger.info(f"Closed existing connection for {player_id} in game {self.game_id}")
            
            # Create new connection
            conn = PlayerConnection(
                websocket=websocket,
                player_id=player_id,
                game_id=self.game_id,
                is_spectator=is_spectator
            )
            self.connections[player_id] = conn
            self.last_activity = time.time()
            
            logger.info(f"Player {player_id} connected to game {self.game_id} (spectator: {is_spectator})")
            
            # Notify others of new connection
            await self.broadcast({
                "type": "player_connected",
                "player_id": player_id,
                "timestamp": datetime.now().isoformat()
            }, exclude={player_id})
            
            return conn
    
    async def remove_connection(self, player_id: str):
        """Remove a player connection from the room"""
        async with self._lock:
            if player_id in self.connections:
                conn = self.connections.pop(player_id)
                self.last_activity = time.time()
                
                logger.info(f"Player {player_id} disconnected from game {self.game_id}")
                
                # Notify others of disconnection
                await self.broadcast({
                    "type": "player_disconnected",
                    "player_id": player_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                return conn
            return None
    
    async def broadcast(self, message: Dict[str, Any], exclude: Set[str] = None):
        """Broadcast a message to all connections in the room"""
        if exclude is None:
            exclude = set()
        
        # Add metadata
        message["game_id"] = self.game_id
        message["server_time"] = time.time()
        
        # Send to all connections except excluded
        disconnected = []
        for player_id, conn in self.connections.items():
            if player_id not in exclude:
                success = await conn.send_json(message)
                if not success:
                    disconnected.append(player_id)
        
        # Clean up disconnected clients
        for player_id in disconnected:
            await self.remove_connection(player_id)
        
        self.last_activity = time.time()
    
    async def send_to_player(self, player_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific player"""
        if player_id in self.connections:
            message["game_id"] = self.game_id
            message["server_time"] = time.time()
            return await self.connections[player_id].send_json(message)
        return False
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connections)
    
    def get_player_ids(self) -> Set[str]:
        """Get all connected player IDs"""
        return set(self.connections.keys())
    
    def is_empty(self) -> bool:
        """Check if room has no connections"""
        return len(self.connections) == 0
    
    def get_info(self) -> Dict[str, Any]:
        """Get room information"""
        return {
            "game_id": self.game_id,
            "connections": len(self.connections),
            "players": list(self.connections.keys()),
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "uptime_seconds": time.time() - self.created_at
        }


class WebSocketManager:
    """Global WebSocket connection manager"""
    
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        
    async def start(self):
        """Start the manager and background tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_empty_rooms())
        logger.info("WebSocket manager started")
    
    async def stop(self):
        """Stop the manager and clean up"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for room in self.rooms.values():
            for conn in list(room.connections.values()):
                try:
                    await conn.websocket.close()
                except:
                    pass
        
        logger.info("WebSocket manager stopped")
    
    async def connect(self, game_id: str, player_id: str, websocket: WebSocket, is_spectator: bool = False) -> PlayerConnection:
        """Connect a player to a game room"""
        async with self._lock:
            # Create room if it doesn't exist
            if game_id not in self.rooms:
                self.rooms[game_id] = GameRoom(game_id)
                logger.info(f"Created new game room: {game_id}")
            
            room = self.rooms[game_id]
        
        # Add connection to room (room handles its own locking)
        return await room.add_connection(player_id, websocket, is_spectator)
    
    async def disconnect(self, game_id: str, player_id: str):
        """Disconnect a player from a game room"""
        if game_id in self.rooms:
            room = self.rooms[game_id]
            await room.remove_connection(player_id)
    
    async def broadcast_to_game(self, game_id: str, message: Dict[str, Any], exclude: Set[str] = None):
        """Broadcast a message to all players in a game"""
        if game_id in self.rooms:
            await self.rooms[game_id].broadcast(message, exclude)
        else:
            logger.warning(f"Attempted to broadcast to non-existent game room: {game_id}")
    
    async def send_to_player(self, game_id: str, player_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific player in a game"""
        if game_id in self.rooms:
            return await self.rooms[game_id].send_to_player(player_id, message)
        return False
    
    def get_room_info(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific room"""
        if game_id in self.rooms:
            return self.rooms[game_id].get_info()
        return None
    
    def get_all_rooms_info(self) -> Dict[str, Any]:
        """Get information about all rooms"""
        return {
            "total_rooms": len(self.rooms),
            "total_connections": sum(room.get_connection_count() for room in self.rooms.values()),
            "rooms": {
                game_id: room.get_info()
                for game_id, room in self.rooms.items()
            }
        }
    
    async def _cleanup_empty_rooms(self):
        """Background task to clean up empty rooms"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                async with self._lock:
                    empty_rooms = [
                        game_id for game_id, room in self.rooms.items()
                        if room.is_empty() and (time.time() - room.last_activity) > 300  # 5 minutes
                    ]
                    
                    for game_id in empty_rooms:
                        del self.rooms[game_id]
                        logger.info(f"Cleaned up empty room: {game_id}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")


# Global instance
websocket_manager = WebSocketManager()