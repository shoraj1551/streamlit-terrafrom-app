"""
Database Query Optimization Module

Provides query profiling, optimization utilities, and pagination helpers.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Query
import time
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryProfiler:
    """
    SQLAlchemy query profiler for performance monitoring
    """
    
    def __init__(self, slow_query_threshold: float = 1.0):
        """
        Initialize query profiler
        
        Args:
            slow_query_threshold: Threshold in seconds for slow query logging
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_stats = []
    
    def setup_profiling(self, engine: Engine):
        """
        Setup query profiling on SQLAlchemy engine
        
        Args:
            engine: SQLAlchemy engine
        """
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - conn.info['query_start_time'].pop()
            
            # Log slow queries
            if total_time > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected ({total_time:.2f}s): {statement[:200]}"
                )
            
            # Store query stats
            self.query_stats.append({
                'statement': statement[:500],
                'duration': total_time,
                'timestamp': time.time()
            })
            
            # Keep only last 1000 queries
            if len(self.query_stats) > 1000:
                self.query_stats = self.query_stats[-1000:]
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get slowest queries
        
        Args:
            limit: Number of queries to return
            
        Returns:
            List of slow query dictionaries
        """
        sorted_queries = sorted(
            self.query_stats,
            key=lambda x: x['duration'],
            reverse=True
        )
        return sorted_queries[:limit]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """
        Get query statistics
        
        Returns:
            Dictionary with query stats
        """
        if not self.query_stats:
            return {
                'total_queries': 0,
                'avg_duration': 0,
                'max_duration': 0,
                'slow_queries': 0
            }
        
        durations = [q['duration'] for q in self.query_stats]
        
        return {
            'total_queries': len(self.query_stats),
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'slow_queries': len([d for d in durations if d > self.slow_query_threshold])
        }


class Paginator:
    """
    Pagination helper for large result sets
    """
    
    @staticmethod
    def paginate(
        query: Query,
        page: int = 1,
        per_page: int = 50,
        max_per_page: int = 100
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Paginate query results
        
        Args:
            query: SQLAlchemy query
            page: Page number (1-indexed)
            per_page: Items per page
            max_per_page: Maximum items per page
            
        Returns:
            Tuple of (items, pagination_info)
        """
        # Validate and limit per_page
        per_page = min(per_page, max_per_page)
        page = max(1, page)
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # Get page items
        items = query.limit(per_page).offset(offset).all()
        
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None
        }
        
        return items, pagination_info


class QueryOptimizer:
    """
    Query optimization utilities
    """
    
    @staticmethod
    def add_indexes_for_deployments(engine: Engine):
        """
        Add optimized indexes for deployment queries
        
        Args:
            engine: SQLAlchemy engine
        """
        with engine.connect() as conn:
            # Index for status filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_deployments_status_created
                ON deployments(status, created_at DESC)
            """))
            
            # Index for user filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_deployments_user_created
                ON deployments(user_email, created_at DESC)
            """))
            
            # Index for provider filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_deployments_provider_created
                ON deployments(provider, created_at DESC)
            """))
            
            # Composite index for common queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_deployments_composite
                ON deployments(user_email, status, created_at DESC)
            """))
            
            conn.commit()
            
        logger.info("✅ Created optimized indexes for deployments")
    
    @staticmethod
    def add_indexes_for_audit_logs(engine: Engine):
        """
        Add optimized indexes for audit log queries
        
        Args:
            engine: SQLAlchemy engine
        """
        with engine.connect() as conn:
            # Index for event type filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_type_timestamp
                ON audit_events(event_type, timestamp DESC)
            """))
            
            # Index for user filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_user_timestamp
                ON audit_events(user_id, timestamp DESC)
            """))
            
            # Index for severity filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_events_severity_timestamp
                ON audit_events(severity, timestamp DESC)
            """))
            
            conn.commit()
            
        logger.info("✅ Created optimized indexes for audit logs")
    
    @staticmethod
    def analyze_query_plan(engine: Engine, query_sql: str) -> str:
        """
        Analyze query execution plan (PostgreSQL)
        
        Args:
            engine: SQLAlchemy engine
            query_sql: SQL query to analyze
            
        Returns:
            Query execution plan
        """
        with engine.connect() as conn:
            result = conn.execute(text(f"EXPLAIN ANALYZE {query_sql}"))
            plan = "\n".join([row[0] for row in result])
            return plan


# Global profiler instance
_query_profiler = None


def get_query_profiler() -> QueryProfiler:
    """Get global query profiler instance"""
    global _query_profiler
    if _query_profiler is None:
        _query_profiler = QueryProfiler()
    return _query_profiler


def setup_query_optimization(engine: Engine):
    """
    Setup query optimization for the application
    
    Args:
        engine: SQLAlchemy engine
    """
    # Setup profiling
    profiler = get_query_profiler()
    profiler.setup_profiling(engine)
    
    # Add indexes
    optimizer = QueryOptimizer()
    try:
        optimizer.add_indexes_for_deployments(engine)
        optimizer.add_indexes_for_audit_logs(engine)
    except Exception as e:
        logger.warning(f"Could not create indexes (may already exist): {e}")
    
    logger.info("✅ Query optimization setup complete")
