from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .store import Store


class Step:
    """Represents a single step within an X-Ray run"""
    
    def __init__(self, step_id: str, run_id: str, name: str, index: int,
                 input_data: Dict[str, Any], reasoning: Optional[str],
                 store: "Store"):
        self.step_id = step_id
        self.run_id = run_id
        self.name = name
        self.index = index
        self._input_data = input_data
        self._reasoning = reasoning
        self._store = store
        self._started_at = datetime.utcnow()
        self._output: Optional[Dict[str, Any]] = None
        self._filters_applied: Optional[Dict[str, Any]] = None
        self._evaluations: List[Dict[str, Any]] = []
        self._error: Optional[str] = None
    
    def set_output(self, output: Dict[str, Any]):
        """
        Set the output data for this step.
        
        Args:
            output: Output data dictionary
        """
        self._output = output
    
    def set_filters(self, filters: Dict[str, Any]):
        """
        Set the filters applied in this step.
        
        Args:
            filters: Dictionary describing filters applied
        """
        self._filters_applied = filters
    
    def add_evaluation(self, evaluation: Dict[str, Any]):
        """
        Add a candidate evaluation result.
        
        Args:
            evaluation: Dictionary with evaluation details (e.g., candidate data,
                       filter_results, qualified status, etc.)
        """
        self._evaluations.append(evaluation)
    
    def add_evaluations(self, evaluations: List[Dict[str, Any]]):
        """
        Add multiple candidate evaluation results.
        
        Args:
            evaluations: List of evaluation dictionaries
        """
        self._evaluations.extend(evaluations)
    
    def _set_error(self, error: str):
        """Mark this step as failed with an error"""
        self._error = error
    
    def _finish(self):
        """Finish this step and persist all data"""
        ended_at = datetime.utcnow()
        duration_ms = int((ended_at - self._started_at).total_seconds() * 1000)
        status = "error" if self._error else "success"
        
        self._store.finish_step(
            step_id=self.step_id,
            ended_at=ended_at,
            duration_ms=duration_ms,
            status=status,
            output=self._output,
            filters_applied=self._filters_applied,
            evaluations=self._evaluations if self._evaluations else None,
            error=self._error
        )

