import logging
import uvicorn
from fastapi import FastAPI
from shared.database import engine, Base
from question_generation.presentation.routes import router as questions_router

# Configure root logger to output INFO and ERROR logs to the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Auto-generate database tables on startup.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OEA Backend API",
    description="AI-driven Question Ingestion and Question Generation service endpoints.",
    version="1.0.0"
)

# Register routers
app.include_router(questions_router)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "OEA Backend API",
        "database": "connected"
    }

if __name__ == "__main__":
    # Boot server on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
