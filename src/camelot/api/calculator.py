"""Calculator API endpoints."""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Optional
import time
import uuid

from ..core.cache_init import get_cached_calculator, get_cache_manager
from .models import CalculateRequest, CalculateResponse, HealthResponse, BatchCalculateRequest, BatchCalculateResponse
from ..core.cache_storage import CacheStorage
from ..core.calculator_logger import calculator_logger
import os
import glob
from pathlib import Path
from datetime import datetime


router = APIRouter(prefix="/api", tags=["calculator"])
calculator = get_cached_calculator()
cache_manager: Optional['CacheManager'] = None


@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict:
    """Check if the API is healthy and poker_knight is available."""
    try:
        # Try a simple calculation to verify poker_knightNG works
        test_result = calculator.calculate_no_cache(["A♠", "K♠"], 1)
        poker_available = True
        
        # Get GPU server status
        gpu_status = None
        try:
            gpu_status = calculator.health_check()
        except:
            pass
    except:
        poker_available = False
        gpu_status = None
    
    return {
        "status": "healthy",
        "version": "0.0.1",
        "poker_knight_available": poker_available,
        "gpu_status": gpu_status
    }


@router.post("/calculate", response_model=CalculateResponse)
async def calculate_poker_odds(calc_request: CalculateRequest, request: Request) -> Dict:
    """
    Calculate poker hand probabilities.
    
    This endpoint accepts hero's hole cards, number of opponents, and optional board cards,
    then returns win/tie/loss probabilities along with detailed statistics.
    """
    # Get session ID from cookies or create new one
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Track timing
    start_time = time.time()
    
    try:
        # Call calculate method with all new parameters
        result = calculator.calculate(
            calc_request.hero_hand,
            calc_request.num_opponents,
            calc_request.board_cards,
            calc_request.simulation_mode,
            calc_request.hero_position,
            calc_request.stack_sizes,
            calc_request.pot_size,
            calc_request.tournament_context,
            calc_request.action_to_hero,
            calc_request.bet_size,
            calc_request.street,
            calc_request.players_to_act,
            calc_request.tournament_stage,
            calc_request.blind_level
        )
        
        
        # Build response with all available fields
        response_data = {
            "success": True,
            "win_probability": result.get("win_probability"),
            "tie_probability": result.get("tie_probability"),
            "loss_probability": result.get("loss_probability"),
            "simulations_run": result.get("simulations_run"),
            "execution_time_ms": result.get("execution_time_ms"),
            "confidence_interval": result.get("confidence_interval"),
            "hand_categories": result.get("hand_categories"),
            "hero_hand": result.get("hero_hand"),
            "board_cards": result.get("board_cards"),
            "num_opponents": result.get("num_opponents"),
            "error": None
        }
        
        # Debug: Log hand_categories
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"API Response - hand_categories: {response_data['hand_categories']}")
        logger.info(f"API Response - hand_categories type: {type(response_data['hand_categories'])}")
        
        # Add all advanced features including new poker_knightNG fields
        advanced_keys = [
            "position_aware_equity", "icm_equity", "multi_way_statistics", 
            "defense_frequencies", "coordination_effects", "stack_to_pot_ratio",
            "tournament_pressure", "fold_equity_estimates", "bubble_factor",
            "bluff_catching_frequency", "range_coordination_score",
            # New poker_knightNG fields
            "spr", "pot_odds", "mdf", "equity_needed", "commitment_threshold",
            "nuts_possible", "draw_combinations", "board_texture_score",
            "equity_vs_range_percentiles", "positional_advantage_score",
            "hand_vulnerability",
            # Cache metadata
            "from_cache", "cache_time_ms", "calculation_time_ms"
        ]
        
        for key in advanced_keys:
            if key in result:
                response_data[key] = result[key]
        
        # Calculate total execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Log the request
        calculator_logger.log_request(
            session_id=session_id,
            user_ip=client_ip,
            request_data=calc_request.dict(),
            response_data=response_data,
            execution_time_ms=execution_time_ms,
            cache_hit=result.get("from_cache", False),
            error=None
        )
        
        return response_data
        
    except ValueError as e:
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Log the error
        calculator_logger.log_request(
            session_id=session_id,
            user_ip=client_ip,
            request_data=calc_request.dict(),
            response_data={},
            execution_time_ms=execution_time_ms,
            cache_hit=False,
            error=str(e)
        )
        
        # Return error response for validation errors
        return {
            "success": False,
            "win_probability": None,
            "tie_probability": None,
            "loss_probability": None,
            "simulations_run": None,
            "execution_time_ms": None,
            "confidence_interval": None,
            "hand_categories": None,
            "hero_hand": calc_request.hero_hand,
            "board_cards": calc_request.board_cards or [],
            "num_opponents": calc_request.num_opponents,
            "error": str(e)
        }
        
    except Exception as e:
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Log the error
        calculator_logger.log_request(
            session_id=session_id,
            user_ip=client_ip,
            request_data=calc_request.dict(),
            response_data={},
            execution_time_ms=execution_time_ms,
            cache_hit=False,
            error=str(e)
        )
        
        # Unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/calculate-batch", response_model=BatchCalculateResponse)
async def calculate_batch(batch_request: BatchCalculateRequest, request: Request) -> Dict:
    """
    Calculate multiple poker hands in batch for efficiency.
    
    This endpoint leverages poker_knightNG's batch processing capability
    to solve multiple problems efficiently with GPU keep-alive.
    """
    # Get session ID and client IP
    session_id = request.cookies.get("session_id", str(uuid.uuid4()))
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Convert CalculateRequest objects to dicts for batch processing
        problems = []
        for req in batch_request.problems:
            problem = {
                "hero_hand": req.hero_hand,
                "num_opponents": req.num_opponents
            }
            
            # Add optional parameters if present
            if req.board_cards:
                problem["board_cards"] = req.board_cards
            if req.simulation_mode != "default":
                problem["simulation_mode"] = req.simulation_mode
            if req.hero_position:
                problem["hero_position"] = req.hero_position
            if req.stack_sizes:
                problem["stack_sizes"] = req.stack_sizes
            if req.pot_size:
                problem["pot_size"] = req.pot_size
            if req.tournament_context:
                problem["tournament_context"] = req.tournament_context
            if req.action_to_hero:
                problem["action_to_hero"] = req.action_to_hero
            if req.bet_size is not None:
                problem["bet_size"] = req.bet_size
            if req.street:
                problem["street"] = req.street
            if req.players_to_act is not None:
                problem["players_to_act"] = req.players_to_act
            if req.tournament_stage:
                problem["tournament_stage"] = req.tournament_stage
            if req.blind_level is not None:
                problem["blind_level"] = req.blind_level
                
            problems.append(problem)
        
        # Use batch calculation
        import time
        start_time = time.time()
        results = calculator.calculate_batch(problems)
        total_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Convert results to CalculateResponse format
        responses = []
        successful = 0
        
        for i, result in enumerate(results):
            if result is None:
                # Failed calculation
                responses.append(None)
            else:
                # Build response data
                response_data = {
                    "success": True,
                    "win_probability": result.get("win_probability"),
                    "tie_probability": result.get("tie_probability"),
                    "loss_probability": result.get("loss_probability"),
                    "simulations_run": result.get("simulations_run"),
                    "execution_time_ms": result.get("execution_time_ms"),
                    "confidence_interval": result.get("confidence_interval"),
                    "hand_categories": result.get("hand_categories"),
                    "hero_hand": result.get("hero_hand"),
                    "board_cards": result.get("board_cards"),
                    "num_opponents": result.get("num_opponents"),
                    "error": None
                }
                
                # Add all advanced features
                advanced_keys = [
                    "position_aware_equity", "icm_equity", "multi_way_statistics", 
                    "defense_frequencies", "coordination_effects", "stack_to_pot_ratio",
                    "tournament_pressure", "fold_equity_estimates", "bubble_factor",
                    "bluff_catching_frequency", "range_coordination_score",
                    "spr", "pot_odds", "mdf", "equity_needed", "commitment_threshold",
                    "nuts_possible", "draw_combinations", "board_texture_score",
                    "equity_vs_range_percentiles", "positional_advantage_score",
                    "hand_vulnerability", "from_cache", "cache_time_ms", "calculation_time_ms"
                ]
                
                for key in advanced_keys:
                    if key in result:
                        response_data[key] = result[key]
                
                responses.append(response_data)
                successful += 1
        
        # Log the batch request
        calculator_logger.log_batch_request(
            session_id=session_id,
            user_ip=client_ip,
            problem_count=len(problems),
            successful_count=successful,
            total_time_ms=total_time
        )
        
        return {
            "success": True,
            "results": responses,
            "total_problems": len(problems),
            "successful_calculations": successful,
            "total_execution_time_ms": total_time,
            "average_execution_time_ms": total_time / len(problems) if problems else 0
        }
        
    except Exception as e:
        # Return error response
        raise HTTPException(status_code=500, detail=f"Batch calculation failed: {str(e)}")


@router.get("/cache-status")
async def get_cache_status() -> Dict:
    """Get current cache statistics."""
    # Get cache stats directly from calculator
    cache_stats = calculator.get_cache_stats()
    
    # Get warming stats from cache manager if available
    if cache_manager:
        warming_stats = cache_manager.get_cache_stats()
        # Show what's being warmed this session, not the total count
        warming_this_session = warming_stats.get('warming_this_session', 0)
        initial_cached = warming_stats.get('initial_cached', 0)
        total_expected = warming_stats.get('total_expected', 0)
        rate = warming_stats.get('rolling_rate', 0)
        is_warming = cache_manager.is_warming()
        
        # Calculate progress
        progress_percent = ((initial_cached + warming_this_session) / total_expected * 100) if total_expected > 0 else 0
    else:
        warming_this_session = 0
        initial_cached = cache_stats.get('sqlite_entries', 0)
        total_expected = 0
        rate = 0
        is_warming = False
        progress_percent = 0
    
    return {
        "status": "active",
        "is_warming": is_warming,
        "warming_this_session": warming_this_session,
        "initial_cached": initial_cached,
        "total_expected": total_expected,
        "progress_percent": round(progress_percent, 1),
        "rate_per_second": round(rate, 1),
        "statistics": {
            **cache_stats,
            "warming": warming_stats if cache_manager else {}
        }
    }


@router.post("/cache-reset")
async def reset_cache() -> Dict:
    """Reset the cache (debugging feature)."""
    try:
        # Clear the cache
        calculator.clear_cache()
        
        # Reset cache manager stats if available
        if cache_manager:
            cache_manager.reset_stats()
        
        return {
            "status": "success",
            "message": "Cache has been reset"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset cache: {str(e)}")


@router.post("/cache-cleanup")
async def cleanup_invalid_cache() -> Dict:
    """Clean up invalid cache entries (entries with empty hand_categories)."""
    try:
        count = calculator.clear_invalid_cache_entries()
        
        return {
            "status": "success",
            "message": f"Cleaned up {count} invalid cache entries",
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clean cache: {str(e)}")


@router.get("/database-info")
async def get_database_info() -> Dict:
    """Get detailed database information and statistics."""
    import sqlite3
    import os
    from datetime import datetime
    
    try:
        # Get cache storage instance
        cache_storage = calculator.cache
        db_path = os.path.expanduser(cache_storage.db_path)
        
        if not os.path.exists(db_path):
            return {
                "status": "error",
                "error": "Database file not found"
            }
        
        # Get file info
        file_stats = os.stat(db_path)
        file_size_mb = file_stats.st_size / (1024 * 1024)
        
        # Connect to database for detailed info
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_info = {}
            for table in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                # Get column info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                table_info[table] = {
                    "row_count": count,
                    "columns": columns
                }
            
            # Get cache entry statistics
            stats = {}
            if "cache_entries" in tables:
                # Age distribution
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN created_at > datetime('now', '-1 day') THEN 1 ELSE 0 END) as last_24h,
                        SUM(CASE WHEN created_at > datetime('now', '-7 days') THEN 1 ELSE 0 END) as last_7d,
                        SUM(CASE WHEN created_at > datetime('now', '-30 days') THEN 1 ELSE 0 END) as last_30d
                    FROM cache_entries
                """)
                age_stats = cursor.fetchone()
                
                # Access statistics
                cursor.execute("""
                    SELECT 
                        MIN(access_count) as min_access,
                        MAX(access_count) as max_access,
                        AVG(access_count) as avg_access,
                        SUM(access_count) as total_access
                    FROM cache_entries
                """)
                access_stats = cursor.fetchone()
                
                # Most accessed entries
                cursor.execute("""
                    SELECT hero_hand, num_opponents, board_cards, access_count
                    FROM cache_entries
                    ORDER BY access_count DESC
                    LIMIT 5
                """)
                top_entries = cursor.fetchall()
                
                stats = {
                    "age_distribution": {
                        "total": age_stats[0] if age_stats else 0,
                        "last_24_hours": age_stats[1] if age_stats else 0,
                        "last_7_days": age_stats[2] if age_stats else 0,
                        "last_30_days": age_stats[3] if age_stats else 0
                    },
                    "access_statistics": {
                        "min_access_count": access_stats[0] if access_stats else 0,
                        "max_access_count": access_stats[1] if access_stats else 0,
                        "avg_access_count": round(access_stats[2], 2) if access_stats and access_stats[2] else 0,
                        "total_accesses": access_stats[3] if access_stats else 0
                    },
                    "most_accessed": [
                        {
                            "hero_hand": entry[0],
                            "opponents": entry[1],
                            "board": entry[2] or "Pre-flop",
                            "access_count": entry[3]
                        } for entry in top_entries
                    ] if top_entries else []
                }
            
            # Get database integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            return {
                "status": "success",
                "database": {
                    "path": db_path,
                    "size_mb": round(file_size_mb, 2),
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "integrity": integrity
                },
                "tables": table_info,
                "statistics": stats
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/database-vacuum")
async def vacuum_database() -> Dict:
    """Vacuum the database to reclaim space and optimize performance."""
    import sqlite3
    import os
    
    try:
        cache_storage = calculator.cache
        db_path = os.path.expanduser(cache_storage.db_path)
        
        # Get size before vacuum
        size_before = os.path.getsize(db_path) / (1024 * 1024)
        
        # Perform vacuum
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")  # Update statistics
            conn.commit()
        finally:
            conn.close()
        
        # Get size after vacuum
        size_after = os.path.getsize(db_path) / (1024 * 1024)
        space_saved = size_before - size_after
        
        return {
            "status": "success",
            "message": "Database vacuum completed successfully",
            "size_before_mb": round(size_before, 2),
            "size_after_mb": round(size_after, 2),
            "space_saved_mb": round(space_saved, 2),
            "space_saved_percent": round((space_saved / size_before) * 100, 1) if size_before > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to vacuum database: {str(e)}")


@router.post("/database-cleanup-old")
async def cleanup_old_entries(days: int = 30) -> Dict:
    """Remove cache entries older than specified days."""
    import sqlite3
    
    try:
        if days < 1:
            raise ValueError("Days must be at least 1")
            
        cache_storage = calculator.cache
        db_path = os.path.expanduser(cache_storage.db_path)
        
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            
            # Count entries to be deleted
            cursor.execute(
                "SELECT COUNT(*) FROM cache_entries WHERE created_at < datetime('now', ?)",
                (f'-{days} days',)
            )
            count = cursor.fetchone()[0]
            
            # Delete old entries
            cursor.execute(
                "DELETE FROM cache_entries WHERE created_at < datetime('now', ?)",
                (f'-{days} days',)
            )
            
            conn.commit()
            
            # Also clear from memory cache if needed
            cache_storage.clear_memory_cache()
            
            return {
                "status": "success",
                "message": f"Removed {count} entries older than {days} days",
                "entries_removed": count
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old entries: {str(e)}")


@router.post("/database-export")
async def export_database_stats() -> Dict:
    """Export database statistics and sample data."""
    import sqlite3
    import json
    from datetime import datetime
    
    try:
        cache_storage = calculator.cache
        db_path = os.path.expanduser(cache_storage.db_path)
        
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            
            # Get summary statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(access_count) as total_accesses,
                    AVG(access_count) as avg_access_count,
                    MIN(created_at) as oldest_entry,
                    MAX(created_at) as newest_entry
                FROM cache_entries
            """)
            summary = cursor.fetchone()
            
            # Get sample entries
            cursor.execute("""
                SELECT cache_key, hero_hand, num_opponents, board_cards, 
                       simulation_mode, access_count, created_at
                FROM cache_entries
                ORDER BY access_count DESC
                LIMIT 100
            """)
            samples = cursor.fetchall()
            
            export_data = {
                "export_date": datetime.now().isoformat(),
                "database_path": db_path,
                "summary": {
                    "total_entries": summary[0] if summary else 0,
                    "total_accesses": summary[1] if summary else 0,
                    "avg_access_count": round(summary[2], 2) if summary and summary[2] else 0,
                    "oldest_entry": summary[3] if summary else None,
                    "newest_entry": summary[4] if summary else None
                },
                "top_100_entries": [
                    {
                        "key": sample[0],
                        "hero_hand": sample[1],
                        "opponents": sample[2],
                        "board": sample[3] or "Pre-flop",
                        "mode": sample[4],
                        "access_count": sample[5],
                        "created": sample[6]
                    } for sample in samples
                ] if samples else []
            }
            
            return {
                "status": "success",
                "data": export_data
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export database: {str(e)}")


@router.get("/logs/list")
async def list_log_files() -> Dict:
    """List available log files."""
    try:
        log_dir = Path("logs")
        if not log_dir.exists():
            return {
                "status": "error",
                "error": "Log directory not found"
            }
        
        log_files = []
        
        # Get all log files
        for log_file in log_dir.glob("*.log*"):
            if log_file.is_file():
                stats = log_file.stat()
                log_files.append({
                    "name": log_file.name,
                    "path": str(log_file),
                    "size_mb": round(stats.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "type": "bug_report" if "bug_report" in log_file.name else (
                        "calculator" if "calculator_requests" in log_file.name else "game"
                    )
                })
        
        # Sort by modified time, newest first
        log_files.sort(key=lambda x: x["modified"], reverse=True)
        
        # Group by type
        game_logs = [f for f in log_files if f["type"] == "game"]
        bug_logs = [f for f in log_files if f["type"] == "bug_report"]
        calc_logs = [f for f in log_files if f["type"] == "calculator"]
        
        return {
            "status": "success",
            "logs": {
                "game": game_logs,
                "bug_reports": bug_logs,
                "calculator": calc_logs,
                "total_count": len(log_files),
                "total_size_mb": round(sum(f["size_mb"] for f in log_files), 2)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/logs/read")
async def read_log_file(
    filename: str,
    lines: int = 100,
    offset: int = 0,
    search: Optional[str] = None
) -> Dict:
    """Read contents of a log file."""
    try:
        # Validate filename to prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")
        
        log_path = Path("logs") / filename
        if not log_path.exists() or not log_path.is_file():
            return {
                "status": "error",
                "error": "Log file not found"
            }
        
        # Read file in reverse for most recent entries first
        all_lines = []
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            filtered_lines = []
            for i, line in enumerate(all_lines):
                if search_lower in line.lower():
                    # Include context lines
                    start = max(0, i - 2)
                    end = min(len(all_lines), i + 3)
                    context = all_lines[start:end]
                    filtered_lines.extend(context)
            all_lines = list(dict.fromkeys(filtered_lines))  # Remove duplicates while preserving order
        
        # Apply pagination
        total_lines = len(all_lines)
        start_idx = offset
        end_idx = min(start_idx + lines, total_lines)
        
        # Reverse to show newest first
        selected_lines = all_lines[start_idx:end_idx]
        
        return {
            "status": "success",
            "file": filename,
            "content": selected_lines,
            "total_lines": total_lines,
            "offset": offset,
            "lines_returned": len(selected_lines),
            "has_more": end_idx < total_lines
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/logs/tail")
async def tail_log_file(filename: str, lines: int = 50) -> Dict:
    """Get the last N lines of a log file."""
    try:
        # Validate filename
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")
        
        log_path = Path("logs") / filename
        if not log_path.exists() or not log_path.is_file():
            return {
                "status": "error",
                "error": "Log file not found"
            }
        
        # Use a more efficient tail implementation for large files
        import subprocess
        try:
            result = subprocess.run(
                ["tail", "-n", str(lines), str(log_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                content = result.stdout.splitlines()
            else:
                # Fallback to Python implementation
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    content = all_lines[-lines:] if len(all_lines) > lines else all_lines
        except:
            # Fallback to Python implementation
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                content = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "status": "success",
            "file": filename,
            "content": content,
            "lines_returned": len(content)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/logs/search-bug-reports")
async def search_bug_reports(query: Optional[str] = None, days: int = 7) -> Dict:
    """Search bug reports within the specified time range."""
    try:
        log_dir = Path("logs")
        bug_reports = []
        
        # Calculate date threshold
        from datetime import datetime, timedelta
        threshold = datetime.now() - timedelta(days=days)
        
        # Search in bug report logs
        for log_file in log_dir.glob("bug_reports*.log"):
            if log_file.is_file():
                stats = log_file.stat()
                if datetime.fromtimestamp(stats.st_mtime) < threshold:
                    continue
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    current_report = None
                    
                    for line in f:
                        if "USER_BUG_REPORT_START" in line:
                            current_report = {
                                "timestamp": "",
                                "description": "",
                                "context": [],
                                "file": log_file.name
                            }
                        elif "USER_BUG_REPORT_END" in line and current_report:
                            # Filter by query if provided
                            if not query or query.lower() in current_report["description"].lower():
                                bug_reports.append(current_report)
                            current_report = None
                        elif current_report:
                            if "Timestamp:" in line:
                                current_report["timestamp"] = line.split("Timestamp:", 1)[1].strip()
                            elif "Description:" in line:
                                current_report["description"] = line.split("Description:", 1)[1].strip()
                            else:
                                current_report["context"].append(line.strip())
        
        # Sort by timestamp, newest first
        bug_reports.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "status": "success",
            "bug_reports": bug_reports[:100],  # Limit to 100 most recent
            "total_found": len(bug_reports),
            "search_query": query,
            "days_searched": days
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/logs/download")
async def download_log(filename: str):
    """Get a log file for download."""
    from fastapi.responses import FileResponse
    
    try:
        # Validate filename
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")
        
        log_path = Path("logs") / filename
        if not log_path.exists() or not log_path.is_file():
            raise HTTPException(status_code=404, detail="Log file not found")
        
        return FileResponse(
            path=str(log_path),
            filename=filename,
            media_type='text/plain'
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gpu-server-status")
async def get_gpu_server_status() -> Dict:
    """Get GPU server statistics and health information."""
    try:
        stats = calculator.get_server_statistics()
        health = calculator.health_check()
        
        return {
            "status": "success",
            "health": health,
            "statistics": stats
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "health": {"status": "unknown"},
            "statistics": {}
        }


@router.get("/calculator-logs")
async def get_calculator_logs(lines: int = 100) -> Dict:
    """Get recent calculator request logs."""
    try:
        logs = calculator_logger.get_recent_logs(lines)
        return {
            "status": "success",
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "logs": []
        }


@router.get("/system-status")
async def get_system_status() -> Dict:
    """Get system status information."""
    import platform
    import os
    from datetime import datetime
    
    try:
        # Get cache stats
        cache_stats = calculator.get_cache_stats()
        
        # Simple memory estimation using resource module
        memory_info = {"status": "available"}
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            memory_info["process_memory_mb"] = usage.ru_maxrss / 1024  # Convert to MB
        except:
            memory_info["status"] = "unavailable"
        
        return {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "system": {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "cpu_count": os.cpu_count(),
                "memory_info": memory_info
            },
            "cache": {
                "total_entries": cache_stats.get('memory_entries', 0) + cache_stats.get('sqlite_entries', 0),
                "hit_rate": round(cache_stats.get('hit_rate', 0), 1),
                "active": True
            },
            "api_version": "0.0.1"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }