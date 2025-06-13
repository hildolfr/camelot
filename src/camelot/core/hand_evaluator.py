"""
Hand evaluation module for Texas Hold'em poker.

Evaluates 7 cards (2 hole + 5 community) to find the best 5-card hand.
Handles ranking, comparison, and tie-breaking.
"""

from typing import List, Tuple, Dict, Optional
from itertools import combinations
from collections import Counter


class HandRank:
    """Hand rankings from highest to lowest."""
    ROYAL_FLUSH = 10
    STRAIGHT_FLUSH = 9
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 7
    FLUSH = 6
    STRAIGHT = 5
    THREE_OF_A_KIND = 4
    TWO_PAIR = 3
    ONE_PAIR = 2
    HIGH_CARD = 1

    NAMES = {
        10: "Royal Flush",
        9: "Straight Flush",
        8: "Four of a Kind",
        7: "Full House",
        6: "Flush",
        5: "Straight",
        4: "Three of a Kind",
        3: "Two Pair",
        2: "One Pair",
        1: "High Card"
    }


class Card:
    """Card representation with rank and suit."""
    RANKS = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
             '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    SUITS = {'♠': 0, '♥': 1, '♦': 2, '♣': 3}
    
    def __init__(self, card_str: str):
        """Initialize from string like 'A♠' or 'K♥'."""
        if len(card_str) < 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        # Handle both formats: 'A♠' and '10♠'
        if card_str[0:2] == '10':
            self.rank = 10
            self.suit = self.SUITS[card_str[2]]
            self.rank_char = 'T'
        else:
            rank_char = card_str[0]
            self.rank_char = rank_char
            self.rank = self.RANKS.get(rank_char)
            self.suit = self.SUITS.get(card_str[1])
        
        if self.rank is None or self.suit is None:
            raise ValueError(f"Invalid card: {card_str}")
    
    def __repr__(self):
        suit_symbols = ['♠', '♥', '♦', '♣']
        return f"{self.rank_char}{suit_symbols[self.suit]}"
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    def __lt__(self, other):
        return self.rank < other.rank


class HandEvaluation:
    """Result of evaluating a poker hand."""
    def __init__(self, rank: int, value: Tuple[int, ...], cards: List[Card], name: str):
        self.rank = rank  # HandRank constant (1-10)
        self.value = value  # Tuple for tie-breaking (e.g., (8, 13, 11) for kings full of jacks)
        self.cards = cards  # The actual 5 cards making up the hand
        self.name = name  # Human-readable name
    
    def __lt__(self, other):
        # Higher rank is better
        if self.rank != other.rank:
            return self.rank < other.rank
        # If same rank, compare values (higher is better)
        return self.value < other.value
    
    def __eq__(self, other):
        return self.rank == other.rank and self.value == other.value
    
    def __repr__(self):
        cards_str = ' '.join(str(c) for c in self.cards)
        return f"{self.name} ({cards_str})"


def evaluate_hand(hole_cards: List[str], community_cards: List[str]) -> HandEvaluation:
    """
    Evaluate the best 5-card poker hand from 7 cards.
    
    Args:
        hole_cards: List of 2 hole card strings (e.g., ['A♠', 'K♠'])
        community_cards: List of 5 community card strings
    
    Returns:
        HandEvaluation object with rank, value, cards, and name
    """
    # Convert all cards to Card objects
    all_cards = [Card(c) for c in hole_cards + community_cards]
    
    # Find best 5-card combination
    best_eval = None
    
    for five_cards in combinations(all_cards, 5):
        eval_result = evaluate_five_cards(list(five_cards))
        if best_eval is None or eval_result > best_eval:
            best_eval = eval_result
    
    return best_eval


def evaluate_five_cards(cards: List[Card]) -> HandEvaluation:
    """Evaluate exactly 5 cards and return the hand ranking."""
    # Sort cards by rank (descending)
    cards = sorted(cards, key=lambda c: c.rank, reverse=True)
    
    # Check for flush
    suits = [c.suit for c in cards]
    is_flush = len(set(suits)) == 1
    
    # Check for straight
    ranks = [c.rank for c in cards]
    is_straight = False
    straight_high = 0
    
    # Regular straight check
    if ranks == list(range(ranks[0], ranks[0]-5, -1)):
        is_straight = True
        straight_high = ranks[0]
    # Check for A-2-3-4-5 (wheel)
    elif ranks == [14, 5, 4, 3, 2]:
        is_straight = True
        straight_high = 5  # In ace-low straight, 5 is high
    
    # Count ranks for pairs, trips, etc.
    rank_counts = Counter(ranks)
    counts = sorted(rank_counts.values(), reverse=True)
    rank_groups = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    
    # Determine hand rank
    if is_straight and is_flush:
        if ranks == [14, 13, 12, 11, 10]:
            return HandEvaluation(HandRank.ROYAL_FLUSH, (10,), cards, "Royal Flush")
        else:
            return HandEvaluation(HandRank.STRAIGHT_FLUSH, (straight_high,), cards, 
                                f"{HandRank.NAMES[HandRank.STRAIGHT_FLUSH]} ({straight_high} high)")
    
    elif counts == [4, 1]:
        # Four of a kind
        quad_rank = rank_groups[0][0]
        kicker = rank_groups[1][0]
        return HandEvaluation(HandRank.FOUR_OF_A_KIND, (quad_rank, kicker), cards,
                            f"Four {get_rank_name(quad_rank)}s")
    
    elif counts == [3, 2]:
        # Full house
        trips_rank = rank_groups[0][0]
        pair_rank = rank_groups[1][0]
        return HandEvaluation(HandRank.FULL_HOUSE, (trips_rank, pair_rank), cards,
                            f"{get_rank_name(trips_rank)}s full of {get_rank_name(pair_rank)}s")
    
    elif is_flush:
        return HandEvaluation(HandRank.FLUSH, tuple(ranks), cards,
                            f"Flush ({get_rank_name(ranks[0])} high)")
    
    elif is_straight:
        return HandEvaluation(HandRank.STRAIGHT, (straight_high,), cards,
                            f"Straight ({straight_high} high)")
    
    elif counts == [3, 1, 1]:
        # Three of a kind
        trips_rank = rank_groups[0][0]
        kickers = [r[0] for r in rank_groups[1:]]
        return HandEvaluation(HandRank.THREE_OF_A_KIND, (trips_rank,) + tuple(kickers), cards,
                            f"Three {get_rank_name(trips_rank)}s")
    
    elif counts == [2, 2, 1]:
        # Two pair
        pair1_rank = rank_groups[0][0]
        pair2_rank = rank_groups[1][0]
        kicker = rank_groups[2][0]
        # Order pairs by rank
        if pair1_rank < pair2_rank:
            pair1_rank, pair2_rank = pair2_rank, pair1_rank
        return HandEvaluation(HandRank.TWO_PAIR, (pair1_rank, pair2_rank, kicker), cards,
                            f"{get_rank_name(pair1_rank)}s and {get_rank_name(pair2_rank)}s")
    
    elif counts == [2, 1, 1, 1]:
        # One pair
        pair_rank = rank_groups[0][0]
        kickers = sorted([r[0] for r in rank_groups[1:]], reverse=True)
        return HandEvaluation(HandRank.ONE_PAIR, (pair_rank,) + tuple(kickers), cards,
                            f"Pair of {get_rank_name(pair_rank)}s")
    
    else:
        # High card
        return HandEvaluation(HandRank.HIGH_CARD, tuple(ranks), cards,
                            f"{get_rank_name(ranks[0])} high")


def get_rank_name(rank: int) -> str:
    """Get the name of a rank (e.g., 14 -> 'Ace')."""
    names = {2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six', 
             7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
             11: 'Jack', 12: 'Queen', 13: 'King', 14: 'Ace'}
    return names.get(rank, str(rank))


def compare_hands(evaluations: Dict[str, HandEvaluation]) -> List[str]:
    """
    Compare multiple hand evaluations and return winner(s).
    
    Args:
        evaluations: Dict mapping player_id to HandEvaluation
    
    Returns:
        List of player_ids who have the best hand (can be multiple for ties)
    """
    if not evaluations:
        return []
    
    # Find the best hand(s)
    best_eval = max(evaluations.values())
    winners = [player_id for player_id, eval in evaluations.items() if eval == best_eval]
    
    return winners


# Convenience function for direct comparison
def get_winning_players(hole_cards_dict: Dict[str, List[str]], 
                       community_cards: List[str]) -> Tuple[List[str], Dict[str, HandEvaluation]]:
    """
    Determine winning player(s) given hole cards and community cards.
    
    Args:
        hole_cards_dict: Dict mapping player_id to their hole cards
        community_cards: List of 5 community cards
    
    Returns:
        Tuple of (winner_ids, all_evaluations)
    """
    evaluations = {}
    
    for player_id, hole_cards in hole_cards_dict.items():
        evaluations[player_id] = evaluate_hand(hole_cards, community_cards)
    
    winners = compare_hands(evaluations)
    
    return winners, evaluations