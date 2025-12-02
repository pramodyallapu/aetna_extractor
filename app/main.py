from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.routes import upload

app = FastAPI(title="PDF Extraction API", version="1.0.0")

# Create required directories if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routes
app.include_router(upload.router)

@app.get("/")
async def read_root():
    return FileResponse("app/templates/index.html")