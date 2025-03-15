import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Import routes
from app.routes.index import router as index_router
from app.routes.query import router as query_router
from app.routes.event import router as event_router

app = FastAPI(title="Global Events Analysis")

# Configure templates and static files
templates = Jinja2Templates(directory="app/templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(index_router)
app.include_router(query_router)
app.include_router(event_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)