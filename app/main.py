from fastapi import FastAPI
from app.routes import query

app = FastAPI()

# app.include_router(query.router, prefix="/query", tags=["Query"])

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
