import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.episodes import router as episodes_router
from app.database.connection import engine
from app.models import Base
from app.config import settings

app = FastAPI(
    title="YourCast API",
    description="API for generating micro-podcasts from news articles",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourcast.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create storage directory and mount static files
os.makedirs(settings.storage_dir, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.storage_dir), name="storage")

# Create tables
Base.metadata.create_all(bind=engine)

app.include_router(episodes_router, prefix="/episodes", tags=["episodes"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)