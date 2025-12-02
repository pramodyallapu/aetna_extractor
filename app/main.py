from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routes import upload

app = FastAPI(title="PDF Extraction API", version="1.0.0")

# Include routes
app.include_router(upload.router)

@app.get("/")
async def read_root():
    return FileResponse("app/templates/index.html")