import uuid
from typing import Optional, Dict, Any
from contextlib import contextmanager
from .run import Run
from .store import Store
from .store.sqlite_store import SQLiteStore


class XRay:
    """Main X-Ray client for capturing decision traces"""
    
    def __init__(self, store: Optional[Store] = None):
        """
        Initialize X-Ray client.
        
        Args:
            store: Optional store instance. If None, creates a default SQLiteStore.
        """
        self._store = store or SQLiteStore()
        self._current_run: Optional[Run] = None
    
    @contextmanager
    def run(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a new X-Ray run context.
        
        Usage:
            with xray.run("competitor_selection", metadata={"product_id": "123"}) as run:
                # ... your pipeline code ...
        
        Args:
            name: Name of the run
            metadata: Optional metadata dictionary
        """
        run_id = str(uuid.uuid4())
        run = Run(run_id=run_id, name=name, metadata=metadata or {}, store=self._store)
        
        try:
            self._store.create_run(
                run_id=run_id,
                name=name,
                metadata=metadata or {}
            )
            self._current_run = run
            yield run
        except Exception as e:
            run._set_error(str(e))
            raise
        finally:
            run._finish()
            self._current_run = None
    
    def get_current_run(self) -> Optional[Run]:
        """Get the currently active run, if any"""
        return self._current_run


# Global instance for convenience
_default_xray = None


def get_xray() -> XRay:
    """Get the default global X-Ray instance"""
    global _default_xray
    if _default_xray is None:
        _default_xray = XRay()
    return _default_xray


def set_xray(xray: XRay):
    """Set the default global X-Ray instance"""
    global _default_xray
    _default_xray = xray

