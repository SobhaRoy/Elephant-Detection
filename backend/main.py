from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, Base
from .routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EleGuard AI - Surveillance Backend",
    version="1.2",
    description="Edge-cloud surveillance engine for North Bengal elephant corridors"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount frontend static assets and serve index.html directly
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/dashboard", summary="Forest Department Operations Dashboard")
def serve_dashboard():
    return FileResponse("frontend/index.html")
