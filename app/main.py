from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from typing import Optional
from app.xray.store import SQLiteStore
from app.demo.competitor_selection import run_competitor_selection_demo

app = FastAPI(title="X-Ray Dashboard")

# Setup templates and static files
templates = Jinja2Templates(directory="app/templates")

# Add custom Jinja2 filters
def tojson_filter(value, indent=2):
    """Convert value to JSON string"""
    return json.dumps(value, indent=indent, default=str)

templates.env.filters["tojson"] = tojson_filter

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize store
store = SQLiteStore()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard home - run list"""
    runs = store.list_runs(limit=50)
    return templates.TemplateResponse("index.html", {"request": request, "runs": runs})


@app.get("/runs/{run_id}", response_class=HTMLResponse)
async def run_detail(request: Request, run_id: str):
    """Dashboard - run detail view"""
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return templates.TemplateResponse("run_detail.html", {"request": request, "run": run})


@app.get("/demo", response_class=HTMLResponse)
async def demo_form(request: Request):
    """Demo form page with input fields"""
    return templates.TemplateResponse("demo_form.html", {"request": request})


@app.post("/demo/run")
async def run_demo(
    product_title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    rating: Optional[float] = Form(None),
    reviews: Optional[int] = Form(None)
):
    """Trigger a demo competitor selection run with optional custom inputs"""
    # Validate inputs
    errors = []
    
    if product_title and len(product_title.strip()) == 0:
        errors.append("Product title cannot be empty")
    if product_title and len(product_title) > 200:
        errors.append("Product title must be 200 characters or less")
    
    if category and len(category.strip()) == 0:
        errors.append("Category cannot be empty")
    if category and len(category) > 100:
        errors.append("Category must be 100 characters or less")
    
    if price is not None:
        if price < 0.01 or price > 10000:
            errors.append("Price must be between $0.01 and $10,000")
    
    if rating is not None:
        if rating < 0 or rating > 5:
            errors.append("Rating must be between 0.0 and 5.0")
    
    if reviews is not None:
        if reviews < 0 or reviews > 10000000:
            errors.append("Reviews must be between 0 and 10,000,000")
    
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    
    # Process and run demo
    run_id = run_competitor_selection_demo(
        product_title=product_title.strip() if product_title else None,
        category=category.strip() if category else None,
        price=float(price) if price is not None else None,
        rating=float(rating) if rating is not None else None,
        reviews=int(reviews) if reviews is not None else None
    )
    return RedirectResponse(url=f"/runs/{run_id}", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

