# Independent Caching Implementation Plan
Date: 2025-01-09

## Current State
Camelot relies entirely on poker_knight's unified cache system for:
- Storing calculation results
- Retrieving cached results
- SQLite persistence at ~/.camelot_cache/poker_cache.db

## Required Components for Independent Caching

### 1. Cache Storage Layer
- [ ] Implement our own SQLite database schema
- [ ] Create in-memory LRU cache with configurable size limits
- [ ] Handle cache persistence and loading on startup

### 2. Cache Key Generation
- [ ] Create normalized cache keys from:
  - Hero hand (sorted, suit-normalized)
  - Number of opponents
  - Board cards (if any)
  - Simulation mode
- [ ] Ensure consistent key generation for equivalent hands

### 3. Cache Integration
- [ ] Intercept calls between PokerCalculator and poker_knight
- [ ] Check cache before calling solve_poker_hand()
- [ ] Store results after calculations
- [ ] Handle cache misses and errors gracefully

### 4. Migration Strategy
- [ ] Export existing cache data from poker_knight's format
- [ ] Import into new Camelot cache format
- [ ] Verify data integrity after migration

### 5. Performance Optimization
- [ ] Implement batch caching operations
- [ ] Add cache compression for storage efficiency
- [ ] Create indexes for fast lookups

## Implementation Priority
1. **High Priority**: Basic caching layer with memory storage
2. **Medium Priority**: SQLite persistence and migration tools
3. **Low Priority**: Advanced features (compression, analytics)

## Estimated Effort
- Basic implementation: 2-3 days
- Full feature parity: 1 week
- Testing and optimization: 3-4 days

## Risk Mitigation
- Keep poker_knight caching as fallback during transition
- Implement feature flags to switch between cache implementations
- Extensive testing with performance benchmarks