"""Test WebSocket game functionality"""

import asyncio
import json
import websockets
import aiohttp
from typing import Dict, Any, List
import uuid


class WebSocketGameTester:
    """Test WebSocket functionality for poker game"""
    
    def __init__(self, base_url: str = "localhost:8000"):
        self.base_url = base_url
        self.http_url = f"http://{base_url}"
        self.ws_url = f"ws://{base_url}"
        
    async def test_basic_connection(self):
        """Test basic WebSocket connection and disconnection"""
        print("\n=== Testing Basic WebSocket Connection ===")
        
        # Start a game first
        game_id = await self.start_game()
        print(f"Started game: {game_id}")
        
        # Connect via WebSocket
        uri = f"{self.ws_url}/api/game/ws/{game_id}/hero"
        try:
            async with websockets.connect(uri) as websocket:
                print("WebSocket connected successfully")
                
                # Wait for connection established message
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Received: {data['type']}")
                
                assert data['type'] == 'connection_established'
                assert 'game_state' in data
                print("✅ Connection established with game state")
                
                # Send ping
                await websocket.send(json.dumps({
                    "type": "ping",
                    "timestamp": 123456
                }))
                
                # Wait for pong
                message = await websocket.recv()
                data = json.loads(message)
                assert data['type'] == 'pong'
                print("✅ Ping/pong working")
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            raise
    
    async def test_concurrent_connections(self):
        """Test multiple WebSocket connections to same game"""
        print("\n=== Testing Concurrent Connections ===")
        
        # Start a game
        game_id = await self.start_game()
        
        # Connect multiple clients
        connections = []
        try:
            # Hero connection
            hero_uri = f"{self.ws_url}/api/game/ws/{game_id}/hero"
            hero_ws = await websockets.connect(hero_uri)
            connections.append(('hero', hero_ws))
            print("Hero connected")
            
            # Spectator connections
            for i in range(3):
                spec_uri = f"{self.ws_url}/api/game/ws/{game_id}/spectator_{i}"
                spec_ws = await websockets.connect(spec_uri)
                connections.append((f'spectator_{i}', spec_ws))
                print(f"Spectator {i} connected")
            
            # Wait for all connection messages
            for name, ws in connections:
                msg = await ws.recv()
                data = json.loads(msg)
                assert data['type'] == 'connection_established'
                print(f"✅ {name} received connection confirmation")
            
            # Send action from hero
            await connections[0][1].send(json.dumps({
                "type": "action",
                "data": {
                    "action": "check",
                    "amount": 0,
                    "request_id": str(uuid.uuid4())
                }
            }))
            
            # All connections should receive the update
            received_updates = []
            for name, ws in connections:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(msg)
                    if data['type'] == 'game_update':
                        received_updates.append(name)
                        print(f"✅ {name} received game update")
                except asyncio.TimeoutError:
                    print(f"❌ {name} did not receive update")
            
            assert len(received_updates) >= 1  # At least hero should get update
            
        finally:
            # Clean up connections
            for _, ws in connections:
                await ws.close()
    
    async def test_action_via_websocket(self):
        """Test sending game actions via WebSocket"""
        print("\n=== Testing WebSocket Actions ===")
        
        # Start game and hand
        game_id = await self.start_game()
        await self.start_hand(game_id)
        
        uri = f"{self.ws_url}/api/game/ws/{game_id}/hero"
        async with websockets.connect(uri) as websocket:
            # Wait for connection
            msg = await websocket.recv()
            data = json.loads(msg)
            initial_state = data['game_state']
            
            print(f"Initial phase: {initial_state['phase']}")
            print(f"Action on position: {initial_state['action_on']}")
            
            # Find hero player
            hero = next(p for p in initial_state['players'] if not p['is_ai'])
            
            # If it's hero's turn, make an action
            if initial_state['action_on'] == hero['position']:
                print("It's hero's turn, sending check action")
                
                await websocket.send(json.dumps({
                    "type": "action",
                    "data": {
                        "action": "check",
                        "amount": 0,
                        "request_id": str(uuid.uuid4())
                    }
                }))
                
                # Wait for game update
                msg = await websocket.recv()
                data = json.loads(msg)
                
                if data['type'] == 'game_update':
                    print("✅ Received game update after action")
                    new_state = data['state']
                    print(f"New action on position: {new_state['action_on']}")
                elif data['type'] == 'action_error':
                    print(f"❌ Action error: {data['error']}")
                else:
                    print(f"Unexpected message type: {data['type']}")
    
    async def test_reconnection(self):
        """Test reconnection after disconnect"""
        print("\n=== Testing Reconnection ===")
        
        game_id = await self.start_game()
        uri = f"{self.ws_url}/api/game/ws/{game_id}/hero"
        
        # First connection
        ws1 = await websockets.connect(uri)
        msg = await ws1.recv()
        data = json.loads(msg)
        assert data['type'] == 'connection_established'
        print("✅ First connection established")
        
        # Disconnect
        await ws1.close()
        print("Disconnected")
        
        # Reconnect
        ws2 = await websockets.connect(uri)
        msg = await ws2.recv()
        data = json.loads(msg)
        assert data['type'] == 'connection_established'
        print("✅ Reconnection successful")
        
        # Should receive current game state
        assert 'game_state' in data
        print("✅ Received current game state on reconnection")
        
        await ws2.close()
    
    async def start_game(self) -> str:
        """Start a new game via HTTP API"""
        async with aiohttp.ClientSession() as session:
            config = {
                "players": 3,
                "heroStack": 100,
                "opponentStacks": [100, 100],
                "difficulty": "medium",
                "bigBlind": 2
            }
            
            async with session.post(f"{self.http_url}/api/game/start", json=config) as resp:
                data = await resp.json()
                return data['state']['game_id']
    
    async def start_hand(self, game_id: str):
        """Start a new hand via HTTP API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.http_url}/api/game/{game_id}/new-hand") as resp:
                data = await resp.json()
                return data


async def main():
    """Run all WebSocket tests"""
    tester = WebSocketGameTester()
    
    try:
        await tester.test_basic_connection()
        await tester.test_action_via_websocket()
        await tester.test_concurrent_connections()
        await tester.test_reconnection()
        
        print("\n✅ All WebSocket tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())