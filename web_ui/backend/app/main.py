from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import agents

app = FastAPI(
    title="FractFlow UI Backend",
    description="Backend server for the FractFlow Web UI, providing agent discovery and interactive terminals.",
    version="0.1.0",
)

# Configure CORS
origins = [
    "*",  # Allow all origins during development to enable LAN access
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(agents.router, prefix="/api", tags=["agents"])

@app.get("/")
async def root():
    return {"message": "Welcome to the FractFlow UI Backend. Visit /docs for API documentation."} 