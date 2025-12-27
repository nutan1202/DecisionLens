import json
import sqlite3
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path


class SQLiteStore:
    """SQLite implementation of X-Ray store"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite store.
        
        Args:
            db_path: Path to SQLite database file. If None, uses XRAY_DB_PATH env var or defaults to "xray.db"
        """
        if db_path is None:
            db_path = os.getenv("XRAY_DB_PATH", "xray.db")
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    duration_ms INTEGER,
                    status TEXT NOT NULL,
                    metadata TEXT,
                    error TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    duration_ms INTEGER,
                    status TEXT NOT NULL,
                    input TEXT,
                    output TEXT,
                    reasoning TEXT,
                    filters_applied TEXT,
                    evaluations TEXT,
                    error TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_run_id ON steps(run_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at DESC)")
            
            conn.commit()
        finally:
            conn.close()
    
    def create_run(self, run_id: str, name: str, metadata: Dict[str, Any]):
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO runs (id, name, started_at, status, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                run_id,
                name,
                datetime.utcnow().isoformat(),
                "running",
                json.dumps(metadata)
            ))
            conn.commit()
        finally:
            conn.close()
    
    def finish_run(self, run_id: str, ended_at: datetime, duration_ms: int,
                   status: str, error: Optional[str] = None):
        conn = self._get_connection()
        try:
            conn.execute("""
                UPDATE runs
                SET ended_at = ?, duration_ms = ?, status = ?, error = ?
                WHERE id = ?
            """, (
                ended_at.isoformat(),
                duration_ms,
                status,
                error,
                run_id
            ))
            conn.commit()
        finally:
            conn.close()
    
    def create_step(self, step_id: str, run_id: str, name: str, index: int,
                    input_data: Dict[str, Any], reasoning: Optional[str]):
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO steps (id, run_id, name, step_index, started_at, status, input, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                step_id,
                run_id,
                name,
                index,
                datetime.utcnow().isoformat(),
                "running",
                json.dumps(input_data),
                reasoning
            ))
            conn.commit()
        finally:
            conn.close()
    
    def finish_step(self, step_id: str, ended_at: datetime, duration_ms: int,
                    status: str, output: Optional[Dict[str, Any]] = None,
                    filters_applied: Optional[Dict[str, Any]] = None,
                    evaluations: Optional[List[Dict[str, Any]]] = None,
                    error: Optional[str] = None):
        conn = self._get_connection()
        try:
            conn.execute("""
                UPDATE steps
                SET ended_at = ?, duration_ms = ?, status = ?,
                    output = ?, filters_applied = ?, evaluations = ?, error = ?
                WHERE id = ?
            """, (
                ended_at.isoformat(),
                duration_ms,
                status,
                json.dumps(output) if output else None,
                json.dumps(filters_applied) if filters_applied else None,
                json.dumps(evaluations) if evaluations else None,
                error,
                step_id
            ))
            conn.commit()
        finally:
            conn.close()
    
    def list_runs(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("""
                SELECT * FROM runs
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            runs = []
            for row in rows:
                run = dict(row)
                if run["metadata"]:
                    try:
                        run["metadata"] = json.loads(run["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        run["metadata"] = {}
                else:
                    run["metadata"] = {}
                runs.append(run)
            return runs
        finally:
            conn.close()
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                return None
            
            run = dict(row)
            if run["metadata"]:
                try:
                    run["metadata"] = json.loads(run["metadata"])
                except (json.JSONDecodeError, TypeError):
                    run["metadata"] = {}
            else:
                run["metadata"] = {}
            
            # Get steps
            step_rows = conn.execute("""
                SELECT * FROM steps
                WHERE run_id = ?
                ORDER BY step_index ASC
            """, (run_id,)).fetchall()
            
            steps = []
            for step_row in step_rows:
                step = dict(step_row)
                # Map step_index back to index for compatibility
                if "step_index" in step:
                    step["index"] = step["step_index"]
                
                # Parse JSON fields with error handling
                if step.get("input"):
                    try:
                        step["input"] = json.loads(step["input"])
                    except (json.JSONDecodeError, TypeError):
                        step["input"] = {}
                else:
                    step["input"] = {}
                
                if step.get("output"):
                    try:
                        step["output"] = json.loads(step["output"])
                    except (json.JSONDecodeError, TypeError):
                        step["output"] = {}
                else:
                    step["output"] = {}
                
                if step.get("filters_applied"):
                    try:
                        step["filters_applied"] = json.loads(step["filters_applied"])
                    except (json.JSONDecodeError, TypeError):
                        step["filters_applied"] = None
                else:
                    step["filters_applied"] = None
                
                if step.get("evaluations"):
                    try:
                        step["evaluations"] = json.loads(step["evaluations"])
                    except (json.JSONDecodeError, TypeError):
                        step["evaluations"] = None
                else:
                    step["evaluations"] = None
                
                steps.append(step)
            
            run["steps"] = steps
            return run
        finally:
            conn.close()

