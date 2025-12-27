from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime

from .sqlite_store import SQLiteStore

__all__ = ["Store", "SQLiteStore"]


class Store(ABC):
    """Abstract interface for X-Ray data storage"""
    
    @abstractmethod
    def create_run(self, run_id: str, name: str, metadata: Dict[str, Any]):
        """Create a new run"""
        pass
    
    @abstractmethod
    def finish_run(self, run_id: str, ended_at: datetime, duration_ms: int,
                   status: str, error: Optional[str] = None):
        """Finish a run"""
        pass
    
    @abstractmethod
    def create_step(self, step_id: str, run_id: str, name: str, index: int,
                    input_data: Dict[str, Any], reasoning: Optional[str]):
        """Create a new step"""
        pass
    
    @abstractmethod
    def finish_step(self, step_id: str, ended_at: datetime, duration_ms: int,
                    status: str, output: Optional[Dict[str, Any]] = None,
                    filters_applied: Optional[Dict[str, Any]] = None,
                    evaluations: Optional[List[Dict[str, Any]]] = None,
                    error: Optional[str] = None):
        """Finish a step"""
        pass
    
    @abstractmethod
    def list_runs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent runs"""
        pass
    
    @abstractmethod
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a run with all its steps"""
        pass

