"""Debug tool for inspecting game state and troubleshooting issues"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime


class GameStateInspector:
    """Tool for debugging and inspecting live game states"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    async def inspect_game(self, game_id: str):
        """Comprehensive game state inspection"""
        async with aiohttp.ClientSession() as session:
            print(f"\n{'='*80}")
            print(f"GAME STATE INSPECTION - {game_id}")
            print(f"Time: {datetime.now().isoformat()}")
            print(f"{'='*80}\n")
            
            # Get game state
            state = await self._get_game_state(session, game_id)
            if not state:
                print("ERROR: Could not retrieve game state")
                return
            
            # Basic info
            print("=== GAME INFO ===")
            print(f"Game ID: {state['game_id']}")
            print(f"Phase: {state['phase']}")
            print(f"Hand Number: {state['hand_number']}")
            print(f"Board Cards: {state.get('board_cards', [])}")
            print(f"Current Bet: ${state['current_bet']}")
            print(f"Min Raise: ${state['min_raise']}")
            print(f"Action On: Position {state['action_on']}")
            
            # Pot info
            print("\n=== POTS ===")
            pots = state.get('pots', [])
            total_pot = sum(pot['amount'] for pot in pots)
            print(f"Total Pot: ${total_pot}")
            for i, pot in enumerate(pots):
                print(f"  Pot {i+1}: ${pot['amount']} - Eligible: {pot['eligible_players']}")
            
            # Player states
            print("\n=== PLAYERS ===")
            total_chips_in_play = 0
            for p in state['players']:
                status = []
                if p['has_folded']:
                    status.append("FOLDED")
                if p['stack'] == 0:
                    status.append("ALL-IN")
                if state['action_on'] == p['position']:
                    status.append("TO ACT")
                
                status_str = f" [{', '.join(status)}]" if status else ""
                print(f"Position {p['position']} - {p['name']}{status_str}")
                print(f"  Stack: ${p['stack']}")
                print(f"  Current Bet: ${p['current_bet']}")
                print(f"  Hole Cards: {p['hole_cards']}")
                print(f"  Last Action: {p['last_action'] or 'None'}")
                
                total_chips_in_play += p['stack'] + p['current_bet']
            
            print(f"\nTotal Chips in Play: ${total_chips_in_play}")
            
            # Get monitoring metrics
            await self._check_game_health(session, game_id)
            
            # Get hand history
            await self._show_recent_hands(session, game_id)
    
    async def monitor_game(self, game_id: str, interval: int = 2):
        """Live monitoring of game state changes"""
        print(f"Starting live monitoring of game {game_id}")
        print("Press Ctrl+C to stop\n")
        
        last_state = None
        
        try:
            while True:
                async with aiohttp.ClientSession() as session:
                    state = await self._get_game_state(session, game_id)
                    
                    if not state:
                        print("ERROR: Could not retrieve game state")
                        await asyncio.sleep(interval)
                        continue
                    
                    # Check for changes
                    if last_state:
                        changes = self._detect_changes(last_state, state)
                        if changes:
                            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] State Changes Detected:")
                            for change in changes:
                                print(f"  - {change}")
                    
                    last_state = state
                    await asyncio.sleep(interval)
                    
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
    
    async def check_chip_integrity(self, game_id: str):
        """Detailed chip integrity check"""
        async with aiohttp.ClientSession() as session:
            print(f"\n{'='*60}")
            print("CHIP INTEGRITY CHECK")
            print(f"{'='*60}\n")
            
            state = await self._get_game_state(session, game_id)
            if not state:
                return
            
            # Calculate expected chips (this should match game config)
            # For now, just check that chips are consistent
            player_chips = sum(p['stack'] + p['current_bet'] for p in state['players'])
            pot_chips = sum(pot['amount'] for pot in state.get('pots', []))
            
            print(f"Player Chips (stacks + bets): ${player_chips}")
            print(f"Pot Chips: ${pot_chips}")
            print(f"Total Accounted: ${player_chips + pot_chips}")
            
            # Check each player
            print("\nPer-Player Breakdown:")
            for p in state['players']:
                total = p['stack'] + p['current_bet']
                print(f"  {p['name']}: ${p['stack']} stack + ${p['current_bet']} bet = ${total}")
    
    async def _get_game_state(self, session: aiohttp.ClientSession, game_id: str) -> Optional[Dict[str, Any]]:
        """Get current game state"""
        try:
            async with session.get(f"{self.base_url}/api/game/{game_id}/state") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("state")
        except Exception as e:
            print(f"Error getting game state: {e}")
        return None
    
    async def _check_game_health(self, session: aiohttp.ClientSession, game_id: str):
        """Check game health from monitoring"""
        try:
            print("\n=== GAME HEALTH ===")
            async with session.get(f"{self.base_url}/api/game/monitor/game/{game_id}") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"Status: {health['status'].upper()}")
                    print(f"Message: {health['message']}")
                    
                    metrics = health.get('metrics', {})
                    if metrics:
                        print(f"Total Actions: {metrics.get('total_actions', 0)}")
                        print(f"Duplicate Rate: {metrics.get('duplicate_rate', 0):.2%}")
                        print(f"Error Rate: {metrics.get('error_rate', 0):.2%}")
                        
                        breakdown = metrics.get('action_breakdown', {})
                        if breakdown:
                            print("Action Breakdown:")
                            for action, count in breakdown.items():
                                print(f"  {action}: {count}")
        except Exception as e:
            print(f"Could not get health metrics: {e}")
    
    async def _show_recent_hands(self, session: aiohttp.ClientSession, game_id: str):
        """Show recent hand history"""
        try:
            print("\n=== RECENT HANDS ===")
            async with session.get(f"{self.base_url}/api/game/{game_id}/hand-history") as response:
                if response.status == 200:
                    data = await response.json()
                    hands = data.get("hands", [])[:3]  # Show last 3 hands
                    
                    if not hands:
                        print("No completed hands yet")
                        return
                    
                    for hand in hands:
                        print(f"\nHand #{hand['hand_number']}:")
                        print(f"  Board: {' '.join(hand['board_cards'])}")
                        print(f"  Winner: {hand['winner']} (${hand['pot_size']})")
        except Exception as e:
            print(f"Could not get hand history: {e}")
    
    def _detect_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> list:
        """Detect what changed between states"""
        changes = []
        
        # Check phase change
        if old_state['phase'] != new_state['phase']:
            changes.append(f"Phase: {old_state['phase']} -> {new_state['phase']}")
        
        # Check action position
        if old_state['action_on'] != new_state['action_on']:
            changes.append(f"Action moved to position {new_state['action_on']}")
        
        # Check player changes
        for i, (old_p, new_p) in enumerate(zip(old_state['players'], new_state['players'])):
            if old_p['stack'] != new_p['stack']:
                diff = new_p['stack'] - old_p['stack']
                changes.append(f"{new_p['name']}: stack ${old_p['stack']} -> ${new_p['stack']} ({diff:+d})")
            
            if old_p['current_bet'] != new_p['current_bet']:
                changes.append(f"{new_p['name']}: bet ${old_p['current_bet']} -> ${new_p['current_bet']}")
            
            if old_p['last_action'] != new_p['last_action'] and new_p['last_action']:
                changes.append(f"{new_p['name']}: {new_p['last_action']}")
            
            if not old_p['has_folded'] and new_p['has_folded']:
                changes.append(f"{new_p['name']}: FOLDED")
        
        # Check board cards
        if len(old_state.get('board_cards', [])) != len(new_state.get('board_cards', [])):
            changes.append(f"Board: {new_state.get('board_cards', [])}")
        
        return changes


async def main():
    """Main entry point for the inspector tool"""
    if len(sys.argv) < 2:
        print("Usage: python state_inspector.py <command> [game_id] [options]")
        print("\nCommands:")
        print("  inspect <game_id>     - One-time state inspection")
        print("  monitor <game_id>     - Live monitoring")
        print("  chips <game_id>       - Chip integrity check")
        print("  metrics               - Show global metrics")
        return
    
    command = sys.argv[1]
    inspector = GameStateInspector()
    
    if command == "inspect" and len(sys.argv) > 2:
        await inspector.inspect_game(sys.argv[2])
    elif command == "monitor" and len(sys.argv) > 2:
        await inspector.monitor_game(sys.argv[2])
    elif command == "chips" and len(sys.argv) > 2:
        await inspector.check_chip_integrity(sys.argv[2])
    elif command == "metrics":
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/game/monitor/metrics") as response:
                if response.status == 200:
                    metrics = await response.json()
                    print(json.dumps(metrics, indent=2))
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())