# X-Ray: Decision Transparency for Multi-Step Systems

X-Ray is a production-ready Python library and dashboard for debugging non-deterministic, multi-step algorithmic systems. It captures not just *what* happened, but *why* decisions were made at each step.

## Overview

Modern software increasingly relies on multi-step, non-deterministic processes (LLMs, search APIs, filters, ranking algorithms). When the final output is wrong, debugging becomes guesswork. X-Ray provides transparency by capturing:

- **Inputs and outputs** at each step
- **Decision reasoning** (human-readable explanations)
- **Candidate evaluations** with per-rule pass/fail details
- **Filters and constraints** applied
- **Errors and exceptions** with full context

## Features

- **General-purpose SDK** - Works with any multi-step pipeline (domain-agnostic)
- **Clean integration API** - Simple context managers (`run` and `step`)
- **Rich dashboard** - Visualize complete decision trails
- **SQLite storage** - Zero-config persistence with pluggable store interface
- **Exception handling** - Automatic error capture and propagation
- **Production-ready** - Clean architecture, type hints, comprehensive error handling

## Quick Start

### Prerequisites

**Python 3.8+ is required.**

1. **Download Python:** https://www.python.org/downloads/
2. **During installation:** ✅ Check "Add Python to PATH" (important!)
3. **Restart your terminal** after installation

### Setup & Run

**Windows:**
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python -m uvicorn app.main:app --reload
```

**Linux/Mac:**
```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python -m uvicorn app.main:app --reload
```

Then open **http://localhost:8000** in your browser.

**Quick setup script (Windows):**
```bash
setup.bat
# Then follow the printed instructions
```

**Start development server:**
```bash
start_dev.bat  # Windows
# Or manually:
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

### Running the Demo

Click the "Run Demo" button in the dashboard to generate a sample competitor selection workflow with rich X-Ray traces. You can customize inputs via the "Run Demo (Custom)" form.

## Architecture

```
┌─────────────┐
│ Demo Pipeline│  ← Example usage (not part of SDK)
└──────┬──────┘
       │ uses
       ▼
┌─────────────┐
│  X-Ray SDK  │  ← Core library (domain-agnostic)
└──────┬──────┘
       │ writes
       ▼
┌─────────────┐
│  SQLite DB  │  ← Storage layer (pluggable)
└──────┬──────┘
       │ reads
       ▼
┌─────────────┐
│  Dashboard  │  ← Visualization UI
└─────────────┘
```

### Components

- **`app/xray/`** - Core SDK (client, run, step)
  - `client.py` - Main XRay client with context manager API
  - `run.py` - Run context manager for pipeline execution
  - `step.py` - Step context manager for decision points
  - `store/` - Storage abstraction layer
    - `__init__.py` - Abstract Store interface
    - `sqlite_store.py` - SQLite implementation

- **`app/main.py`** - FastAPI server with dashboard routes
- **`app/templates/`** - Jinja2 HTML templates for dashboard
- **`app/demo/`** - Example competitor selection pipeline (demonstrates SDK usage)

## How It Works

### Basic Usage

```python
from app.xray import XRay

xray = XRay()

with xray.run("my_pipeline", metadata={"user_id": "123"}) as run:
    with run.step("step1", input_data={"data": "..."}, reasoning="Processing...") as step:
        result = do_something()
        step.set_output({"result": result})
```

### Advanced Usage: Candidate Evaluation

```python
with run.step("filter_candidates", input_data={"candidates": [...]}) as step:
    # Define filters
    filters = {
        "price_range": {"min": 10, "max": 50},
        "min_rating": {"value": 4.0}
    }
    step.set_filters(filters)
    
    # Evaluate each candidate
    for candidate in candidates:
        evaluation = {
            "candidate_id": candidate["id"],
            "metrics": {"price": candidate["price"], "rating": candidate["rating"]},
            "filter_results": {
                "price_range": {
                    "passed": 10 <= candidate["price"] <= 50,
                    "detail": f"${candidate['price']} is within range"
                },
                "min_rating": {
                    "passed": candidate["rating"] >= 4.0,
                    "detail": f"{candidate['rating']} >= 4.0"
                }
            },
            "qualified": all_passed
        }
        step.add_evaluation(evaluation)
    
    # Set final output
    qualified = [e for e in evaluations if e["qualified"]]
    step.set_output({"qualified_count": len(qualified)})
```

### Complete Integration Example

```python
from app.xray import XRay

def my_algorithm(input_data):
    xray = XRay()
    
    with xray.run("my_algorithm", metadata={"version": "1.0"}) as run:
        # Step 1: Preprocessing
        with run.step("preprocess", input_data=input_data) as step:
            processed = preprocess(input_data)
            step.set_output({"processed": processed})
        
        # Step 2: Generate candidates
        with run.step("generate_candidates") as step:
            candidates = generate(processed)
            step.set_output({"count": len(candidates), "candidates": candidates})
        
        # Step 3: Filter and rank
        with run.step("filter_and_rank", input_data={"candidates": candidates}) as step:
            filters = {"min_score": 0.7}
            step.set_filters(filters)
            
            for candidate in candidates:
                evaluation = {
                    "candidate": candidate["id"],
                    "score": candidate["score"],
                    "qualified": candidate["score"] >= 0.7
                }
                step.add_evaluation(evaluation)
            
            qualified = [c for c in candidates if c["score"] >= 0.7]
            result = max(qualified, key=lambda x: x["score"])
            
            step.set_output({"selected": result})
            return result
```

## Data Model

### Run
- `id` (UUID) - Unique identifier
- `name` - Pipeline name
- `started_at`, `ended_at`, `duration_ms` - Timing information
- `status` - `running` / `success` / `error`
- `metadata` - JSON dictionary for custom fields

### Step
- `id` (UUID) - Unique identifier
- `run_id` - Parent run reference
- `name` - Step name
- `index` - Sequential ordering within run
- `started_at`, `ended_at`, `duration_ms` - Timing information
- `status` - `success` / `error`
- `input` - JSON dictionary (input data)
- `output` - JSON dictionary (output data)
- `reasoning` - Human-readable explanation
- `filters_applied` - JSON dictionary (filters/constraints)
- `evaluations` - JSON array (candidate evaluations)
- `error` - Error message (if failed)

## Dashboard Features

- **Run List** - View all executions with status, duration, timestamps
- **Run Detail** - Complete step-by-step breakdown:
  - Step timeline with status badges
  - Collapsible JSON viewers for inputs/outputs
  - Candidate evaluation tables showing pass/fail reasons
  - Filter details and reasoning
  - Error messages with full context

## Design Principles

### Domain-Agnostic Architecture

The SDK is intentionally designed to be **completely domain-agnostic**. It works with:
- Product recommendation systems
- Fraud detection pipelines
- Content moderation workflows
- ML inference pipelines
- Any multi-step decision process

**Key Design Decisions:**
- **Generic data structures** - All data stored as JSON (no schema constraints)
- **Flexible step names** - Just strings, no domain meaning attached
- **Optional features** - Filters and evaluations are optional
- **Pluggable storage** - Abstract Store interface allows swapping implementations

### Production-Ready Features

- **Exception safety** - Context managers ensure cleanup even on errors
- **Type hints** - Full type annotation coverage
- **Connection management** - Proper resource cleanup in database layer
- **Error propagation** - Errors captured but still propagate to caller
- **Idempotent operations** - Safe to retry operations

## Demo Application

The included demo (`app/demo/competitor_selection.py`) simulates a competitor product selection pipeline:

1. **Keyword Generation** - Mock LLM extracts search keywords from product title
2. **Candidate Search** - Mock API returns product candidates ranked by relevance
3. **Filter & Select** - Applies business rules (price, rating, reviews) and ranks results

Each step captures rich context that makes debugging straightforward. The demo demonstrates:
- Dynamic keyword generation based on input
- Relevance scoring for candidate selection
- Comprehensive evaluation tracking
- Filter application with detailed pass/fail reasons

## API Reference

### XRay Client

```python
class XRay:
    def __init__(self, store: Optional[Store] = None)
    # Creates XRay client with optional custom store
    
    @contextmanager
    def run(self, name: str, metadata: Optional[Dict[str, Any]] = None)
    # Creates a new run context
```

### Run

```python
class Run:
    @contextmanager
    def step(self, name: str, input_data: Optional[Dict[str, Any]] = None, 
             reasoning: Optional[str] = None)
    # Creates a step within the run
```

### Step

```python
class Step:
    def set_output(self, output: Dict[str, Any])
    # Record step output
    
    def set_filters(self, filters: Dict[str, Any])
    # Record filters applied
    
    def add_evaluation(self, evaluation: Dict[str, Any])
    # Add one candidate evaluation
    
    def add_evaluations(self, evaluations: List[Dict[str, Any]])
    # Add multiple evaluations at once
```

## Known Limitations

- **Single-process only** - Not designed for distributed systems (yet)
- **SQLite storage** - Suitable for development/small scale; consider Postgres for production
- **No streaming** - Runs must complete before appearing in dashboard
- **Limited querying** - Basic list/get operations; no advanced filtering/search
- **No authentication** - Dashboard is open; add auth for production use

## Future Improvements

- **Run comparison** - Diff two runs to see what changed
- **Search** - Full-text search within JSON payloads
- **Tags & correlation** - Add tags and correlation IDs for better organization
- **Streaming updates** - Real-time updates via Server-Sent Events
- **Export** - Export runs as JSON/CSV
- **Pluggable stores** - Support for Postgres, S3, etc.
- **OpenTelemetry integration** - Bridge to existing tracing systems
- **Performance metrics** - Track step-level performance over time
- **Async support** - Native async/await support for async pipelines

## Tech Stack

- **Backend**: FastAPI
- **Templating**: Jinja2
- **Styling**: Tailwind CSS (via CDN)
- **Storage**: SQLite (via sqlite3)
- **Python**: 3.8+

## License

MIT
