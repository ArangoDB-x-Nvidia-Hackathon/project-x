from fastapi import FastAPI
from app.routes import query, influence

app = FastAPI(title="Project-X")

app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(influence.router, prefix="/influence", tags=["Influence"])

@app.get("/")
def home():
    return {"message": "Welcome to Project-X API"}
