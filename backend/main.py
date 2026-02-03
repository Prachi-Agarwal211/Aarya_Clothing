from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routes import auth, products, users
from core.config import settings
from database.database import engine, Base
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aarya Clothing API",
    description="Backend API for Aarya Clothing e-commerce platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Next.js frontend and same origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

# Mount static files and serve frontend
if os.path.exists("public"):
    app.mount("/static", StaticFiles(directory="public"), name="static")

# API endpoints
@app.get("/")
async def root():
    return {"message": "Aarya Clothing API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Serve frontend for all other routes (SPA)
@app.get("/{path:path}")
async def serve_frontend(path: str):
    # Try to serve static file first
    if os.path.exists(f"public/{path}"):
        return FileResponse(f"public/{path}")
    
    # Serve index.html for all other routes (SPA routing)
    if os.path.exists("public/index.html"):
        return FileResponse("public/index.html")
    
    # Fallback to API response if frontend not built
    return {"message": "Frontend not built. API is running on /api/*"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
