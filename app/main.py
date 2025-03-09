from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from api.routes import router

# Initialize FastAPI app
app = FastAPI(title="GDELT Event Analysis", 
              description="API for analyzing sentiment and events from GDELT database")

# Set up templates directory for serving HTML
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
