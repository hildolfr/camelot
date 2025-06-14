"""Test concurrent action handling to verify chip integrity"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_CONFIG = {
    "players": 3,
    "heroStack": 100,
    "opponentStacks": [100, 100],
    "difficulty": "medium",
    "bigBlind": 2
}


async def start_game(session: aiohttp.ClientSession) -> str:
    """Start a new game and return game ID"""
    async with session.post(f"{BASE_URL}/api/game/start", json=TEST_CONFIG) as response:
        data = await response.json()
        return data["game_id"]


async def get_game_state(session: aiohttp.ClientSession, game_id: str) -> Dict[str, Any]:
    """Get current game state"""
    async with session.get(f"{BASE_URL}/api/game/{game_id}/state") as response:
        data = await response.json()
        return data["state"]


async def player_action(session: aiohttp.ClientSession, game_id: str, player_id: str, action: str, amount: int = 0) -> Dict[str, Any]:
    """Send a player action"""
    request_id = f"test_{player_id}_{int(time.time() * 1000)}_{action}"
    payload = {
        "player_id": player_id,
        "action": action,
        "amount": amount,
        "request_id": request_id
    }
    
    async with session.post(f"{BASE_URL}/api/game/{game_id}/action", json=payload) as response:
        return await response.json()


async def test_concurrent_fold_scenario():
    """Test the specific scenario where concurrent folds cause chip loss"""
    print("Testing concurrent fold scenario...")
    
    async with aiohttp.ClientSession() as session:
        # Start a new game
        game_id = await start_game(session)
        print(f"Started game: {game_id}")
        
        # Start a new hand
        async with session.post(f"{BASE_URL}/api/game/{game_id}/new-hand") as response:
            hand_data = await response.json()
            print(f"Started hand #{hand_data['state']['hand_number']}")
        
        # Get initial state
        initial_state = await get_game_state(session, game_id)
        initial_total_chips = sum(p["stack"] + p["current_bet"] for p in initial_state["players"])
        print(f"Initial total chips: ${initial_total_chips}")
        
        # Find the hero player
        hero = next(p for p in initial_state["players"] if not p["is_ai"])
        print(f"Hero position: {hero['position']}, stack: ${hero['stack']}")
        
        # If hero is first to act, have them go all-in
        if initial_state["action_on"] == hero["position"]:
            print("Hero going all-in...")
            await player_action(session, game_id, hero["id"], "all_in")
            
            # Get state after all-in
            state_after_allin = await get_game_state(session, game_id)
            
            # Now simulate concurrent fold actions from AI players
            ai_players = [p for p in state_after_allin["players"] if p["is_ai"] and not p["has_folded"]]
            
            print(f"\nSimulating concurrent folds from {len(ai_players)} AI players...")
            
            # Send fold actions concurrently
            fold_tasks = []
            for ai in ai_players:
                if state_after_allin["action_on"] == ai["position"]:
                    # This is the player who should act
                    print(f"Current action on: {ai['name']}")
                    
                    # Create multiple concurrent fold requests for the same player
                    for i in range(3):  # Try to send 3 concurrent folds
                        task = player_action(session, game_id, ai["id"], "fold")
                        fold_tasks.append(task)
            
            # Execute all fold requests concurrently
            if fold_tasks:
                results = await asyncio.gather(*fold_tasks, return_exceptions=True)
                
                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
                error_count = sum(1 for r in results if isinstance(r, dict) and not r.get("success"))
                exception_count = sum(1 for r in results if isinstance(r, Exception))
                
                print(f"\nConcurrent fold results:")
                print(f"  Successful: {success_count}")
                print(f"  Errors: {error_count}")
                print(f"  Exceptions: {exception_count}")
        
        # Wait a bit for any processing to complete
        await asyncio.sleep(1)
        
        # Get final state and check chip integrity
        final_state = await get_game_state(session, game_id)
        final_total_chips = sum(p["stack"] + p["current_bet"] for p in final_state["players"])
        
        print(f"\nFinal total chips: ${final_total_chips}")
        print(f"Chip difference: ${final_total_chips - initial_total_chips}")
        
        # Check each player's chips
        print("\nPlayer chip details:")
        for i, (initial_p, final_p) in enumerate(zip(initial_state["players"], final_state["players"])):
            initial_total = initial_p["stack"] + initial_p["current_bet"]
            final_total = final_p["stack"] + final_p["current_bet"]
            diff = final_total - initial_total
            print(f"  {final_p['name']}: ${initial_total} -> ${final_total} (diff: ${diff})")
        
        # Verify chip integrity
        if initial_total_chips == final_total_chips:
            print("\n✅ CHIP INTEGRITY MAINTAINED!")
        else:
            print(f"\n❌ CHIP INTEGRITY VIOLATION: Lost ${initial_total_chips - final_total_chips}")


async def test_rapid_ai_actions():
    """Test rapid AI actions to ensure no race conditions"""
    print("\n\nTesting rapid AI actions...")
    
    async with aiohttp.ClientSession() as session:
        # Start a new game
        game_id = await start_game(session)
        print(f"Started game: {game_id}")
        
        # Start a new hand
        async with session.post(f"{BASE_URL}/api/game/{game_id}/new-hand") as response:
            hand_data = await response.json()
            print(f"Started hand #{hand_data['state']['hand_number']}")
        
        # Get initial state
        initial_state = await get_game_state(session, game_id)
        initial_total_chips = sum(p["stack"] + p["current_bet"] for p in initial_state["players"])
        
        # If an AI is first to act, send multiple concurrent AI action requests
        if initial_state["players"][initial_state["action_on"]]["is_ai"]:
            ai_player = initial_state["players"][initial_state["action_on"]]
            print(f"\nSending concurrent AI action requests for {ai_player['name']}...")
            
            # Send multiple AI action requests concurrently
            ai_tasks = []
            for i in range(5):  # Try 5 concurrent requests
                task = session.post(f"{BASE_URL}/api/game/{game_id}/ai-action", 
                                   json={"player_id": ai_player["id"]})
                ai_tasks.append(task)
            
            # Execute all requests concurrently
            responses = await asyncio.gather(*ai_tasks, return_exceptions=True)
            
            success_count = 0
            for resp in responses:
                if isinstance(resp, aiohttp.ClientResponse):
                    data = await resp.json()
                    if data.get("success"):
                        success_count += 1
                    resp.close()
            
            print(f"Successful AI actions: {success_count} out of {len(ai_tasks)}")
        
        # Check final chip integrity
        await asyncio.sleep(1)
        final_state = await get_game_state(session, game_id)
        final_total_chips = sum(p["stack"] + p["current_bet"] for p in final_state["players"])
        
        if initial_total_chips == final_total_chips:
            print("✅ CHIP INTEGRITY MAINTAINED!")
        else:
            print(f"❌ CHIP INTEGRITY VIOLATION: Lost ${initial_total_chips - final_total_chips}")


async def main():
    """Run all concurrent action tests"""
    print("=" * 60)
    print("CONCURRENT ACTION HANDLING TESTS")
    print("=" * 60)
    
    try:
        await test_concurrent_fold_scenario()
        await test_rapid_ai_actions()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())