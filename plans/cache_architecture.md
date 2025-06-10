# Camelot Cache Architecture
Date: 2025-01-09

## Overview
With poker_knight v1.7.0 removing its internal caching functionality, Camelot needs its own caching layer to maintain performance. This document outlines the architecture for a hybrid memory/SQLite caching system.

## Design Principles
1. **Performance First**: Sub-5ms response times for cache hits
2. **Complete Game States**: Cache entire poker scenarios from preflop to river
3. **Storage Efficiency**: Store all permutations for flexibility
4. **Simple Interface**: Transparent caching layer over poker_knight
5. **Configurable Limits**: Adjustable memory and disk usage

## Cache Storage Strategy

### Hybrid Architecture
- **In-Memory LRU Cache**: 2GB default (configurable)
  - Hot data for instant access
  - Python's `functools.lru_cache` or custom LRU implementation
  - Automatic eviction of least recently used items
  
- **SQLite Persistence**: 8GB maximum
  - All cached calculations stored persistently
  - Survives application restarts
  - Located at `~/.camelot_cache/camelot_cache.db`

### Data Flow
1. Check memory cache (fastest)
2. If miss, check SQLite cache
3. If miss, calculate via poker_knight
4. Store result in both memory and SQLite
5. Return result

## Cache Key Design

### Key Components
```python
{
    "hero_hand": ["A♠", "K♥"],      # Exact representation
    "num_opponents": 3,               # Integer 1-6
    "board_cards": ["Q♦", "J♣", "10♠"], # Exact representation, [] for preflop
    "simulation_mode": "default"      # "fast", "default", or "precision"
}
```

### Key Generation Rules
1. **No Normalization**: Store exact card representations
2. **All Permutations**: Each unique hand combination stored separately
3. **Exclude Dynamic Data**: No hero_position, stack_sizes, or pot_size in cache key
4. **Consistent Ordering**: Sort board_cards for consistency

### Example Cache Keys
```
# Preflop scenario (no board cards)
"A♠K♥|2||default" → {win: 0.67, tie: 0.01, lose: 0.32}

# Flop scenario (3 board cards)
"A♠K♥|3|Q♦J♣10♠|default" → {win: 0.85, tie: 0.02, lose: 0.13}

# Turn scenario (4 board cards)
"A♠K♥|3|Q♦J♣10♠7♥|default" → {win: 0.91, tie: 0.01, lose: 0.08}

# River scenario (5 board cards - complete game state)
"A♠K♥|3|Q♦J♣10♠7♥2♣|default" → {win: 0.89, tie: 0.01, lose: 0.10}
```

### What Gets Cached
The cache stores **complete game states** including:
- **Hero's exact hand**: Both cards with specific suits
- **Number of opponents**: 1-6 players
- **All community cards**: 
  - Preflop: No board cards
  - Flop: Exactly 3 cards
  - Turn: Exactly 4 cards  
  - River: Exactly 5 cards (complete board)
- **Simulation mode**: Affects accuracy/speed tradeoff
- **Full calculation results**: Win/tie/lose percentages, hand rankings, etc.

Each unique combination of the above creates a separate cache entry. For example, A♠K♥ on a Q♦J♣10♠7♥2♣ board against 3 opponents is a completely different cache entry than the same hand against 2 opponents or with any different board card.

## Cache Schema

### SQLite Schema
```sql
CREATE TABLE cache_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE NOT NULL,
    hero_hand TEXT NOT NULL,
    num_opponents INTEGER NOT NULL,
    board_cards TEXT,
    simulation_mode TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1
);

CREATE INDEX idx_cache_key ON cache_entries(cache_key);
CREATE INDEX idx_last_accessed ON cache_entries(last_accessed);
CREATE INDEX idx_hero_hand ON cache_entries(hero_hand);

CREATE TABLE cache_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Memory Cache Structure
```python
class CacheEntry:
    key: str
    result: Dict[str, float]  # {win, tie, lose, ...}
    timestamp: float
    access_count: int
```

## Implementation Components

### 1. CacheStorage Class
```python
class CacheStorage:
    def __init__(self, memory_limit_mb=2048, db_path="~/.camelot_cache/camelot_cache.db"):
        self.memory_cache = {}  # Or LRU implementation
        self.memory_limit = memory_limit_mb * 1024 * 1024
        self.db_connection = sqlite3.connect(db_path)
        
    def get(self, key: str) -> Optional[Dict]:
        # Check memory first, then SQLite
        
    def set(self, key: str, value: Dict):
        # Store in both memory and SQLite
        
    def evict_memory(self):
        # LRU eviction when memory limit reached
```

### 2. CacheKeyGenerator Class
```python
class CacheKeyGenerator:
    @staticmethod
    def generate_key(hero_hand: List[str], 
                    num_opponents: int,
                    board_cards: Optional[List[str]], 
                    simulation_mode: str) -> str:
        # Format: "hero_hand|num_opponents|board_cards|mode"
        # Example: "A♠K♥|2|Q♦J♣10♠|default"
```

### 3. CachedPokerCalculator Class
```python
class CachedPokerCalculator(PokerCalculator):
    def __init__(self, cache_storage: CacheStorage):
        super().__init__()
        self.cache = cache_storage
        
    def calculate(self, hero_hand, num_opponents, board_cards=None, 
                 simulation_mode="default", **kwargs):
        # Generate cache key (excluding dynamic params)
        cache_key = CacheKeyGenerator.generate_key(
            hero_hand, num_opponents, board_cards, simulation_mode
        )
        
        # Check cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return self._apply_dynamic_params(cached_result, **kwargs)
            
        # Calculate if not cached
        result = super().calculate(hero_hand, num_opponents, 
                                 board_cards, simulation_mode)
        
        # Cache the base result (without dynamic params)
        self.cache.set(cache_key, result)
        
        # Apply dynamic params if provided
        return self._apply_dynamic_params(result, **kwargs)
```

## Cache Warming Strategy

### Current Strategy (Maintained)
1. **Priority Hands**: Premium holdings (AA, KK, AKs, etc.)
2. **Preflop Scenarios**: All 169 starting hands vs 1-6 opponents
3. **Common Boards**: Frequent flop textures
4. **Progressive Streets**: Cache flop → turn → river for common runouts
5. **Background Processing**: Non-blocking thread pool

### Game State Coverage
- **Preflop**: All starting hands × opponent counts
- **Flop**: Common textures (monotone, coordinated, dry boards)
- **Turn**: Natural progressions from cached flops
- **River**: Complete 5-card boards for high-frequency scenarios

### Warming Process
```python
# Use existing CacheManager with new CachedPokerCalculator
cache_manager = CacheManager(CachedPokerCalculator(cache_storage))
cache_manager.start_cache_warming()  # Existing logic works
```

## Migration Plan

### 1. Remove Old Cache
```bash
rm ~/.camelot_cache/poker_cache.db
rm ~/Documents/camelot/poker_knight_unified_cache.db
```

### 2. Update Imports
- Replace PokerCalculator with CachedPokerCalculator
- Remove poker_knight cache imports

### 3. Initialize New Cache
- Create new SQLite database
- Start fresh cache warming process

## Configuration

### Config File (config.py)
```python
CACHE_CONFIG = {
    "memory_limit_mb": int(os.getenv("CAMELOT_CACHE_MEMORY_MB", 2048)),
    "db_max_size_gb": 8,
    "db_path": os.getenv("CAMELOT_CACHE_PATH", "~/.camelot_cache/camelot_cache.db"),
    "enable_cache": True,
    "cache_warming_threads": 4
}
```

## Performance Targets

### Response Times
- Memory cache hit: <1ms
- SQLite cache hit: <5ms  
- Cache miss (calculation): 100-500ms

### Storage Efficiency
- ~24 bytes per cache entry in memory
- ~200 bytes per row in SQLite
- 2GB memory = ~87M entries
- 8GB SQLite = ~42M entries

## Monitoring and Metrics

### Cache Statistics
- Hit rate (memory vs SQLite vs miss)
- Cache size (entries and bytes)
- Average response times
- Most/least accessed entries
- Cache warming progress

### Health Checks
- Database size monitoring
- Memory usage tracking
- Eviction frequency
- Cache effectiveness

## Future Enhancements

### Phase 2 Considerations
1. **Compression**: zlib compression for SQLite storage
2. **Sharding**: Multiple SQLite files for parallel access
3. **Cache Preloading**: Load hot data on startup
4. **Analytics**: Usage patterns and optimization hints

### Not Implemented (By Design)
- Tournament mode caching (too dynamic)
- Position/stack-aware caching (too unique)
- Time-based expiration (probabilities don't change)
- Cache invalidation (immutable data)

## Implementation Timeline

1. **Day 1**: Core cache storage and key generation
2. **Day 2**: Integration with PokerCalculator
3. **Day 3**: Migration and testing
4. **Day 4**: Performance optimization
5. **Day 5**: Monitoring and documentation