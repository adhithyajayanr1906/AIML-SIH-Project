import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import PROJECT_TITLE, PROJECT_DESCRIPTION, VERSION, FRONTEND_DIR
from backend.app.api.endpoints import router as api_router

app = FastAPI(
    title=PROJECT_TITLE,
    description=PROJECT_DESCRIPTION,
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Endpoints
app.include_router(api_router)

# Serve Frontend Static Assets if directory exists
if os.path.exists(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")

@app.get("/", response_class=FileResponse)
def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="frontend/index.html file not found.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
