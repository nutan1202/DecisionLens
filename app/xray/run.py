import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING
from contextlib import contextmanager
from datetime import datetime
from .step import Step

if TYPE_CHECKING:
    from .store import Store


class Run:
    """Represents a single X-Ray execution run"""
    
    def __init__(self, run_id: str, name: str, metadata: Dict[str, Any], store: "Store"):
        self.run_id = run_id
        self.name = name
        self.metadata = metadata
        self._store = store
        self._step_index = 0
        self._started_at = datetime.utcnow()
        self._error: Optional[str] = None
    
    @contextmanager
    def step(self, name: str, input_data: Optional[Dict[str, Any]] = None, 
             reasoning: Optional[str] = None):
        """
        Create a step within this run.
        
        Usage:
            with run.step("keyword_generation", input={"product": "..."}, 
                         reasoning="Extracting keywords...") as step:
                keywords = generate_keywords(...)
                step.set_output({"keywords": keywords})
        
        Args:
            name: Name of the step
            input_data: Optional input data dictionary
            reasoning: Optional reasoning text
        """
        step_id = str(uuid.uuid4())
        step_index = self._step_index
        self._step_index += 1
        
        step = Step(
            step_id=step_id,
            run_id=self.run_id,
            name=name,
            index=step_index,
            input_data=input_data or {},
            reasoning=reasoning,
            store=self._store
        )
        
        try:
            self._store.create_step(
                step_id=step_id,
                run_id=self.run_id,
                name=name,
                index=step_index,
                input_data=input_data or {},
                reasoning=reasoning
            )
            yield step
        except Exception as e:
            step._set_error(str(e))
            raise
        finally:
            step._finish()
    
    def _set_error(self, error: str):
        """Mark this run as failed with an error"""
        self._error = error
    
    def _finish(self):
        """Finish this run"""
        ended_at = datetime.utcnow()
        duration_ms = int((ended_at - self._started_at).total_seconds() * 1000)
        status = "error" if self._error else "success"
        
        self._store.finish_run(
            run_id=self.run_id,
            ended_at=ended_at,
            duration_ms=duration_ms,
            status=status,
            error=self._error
        )

