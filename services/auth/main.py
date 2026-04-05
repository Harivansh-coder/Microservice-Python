# services/auth/main.py
import logging
from fastapi import FastAPI
from models import Base, engine, SessionLocal, User
from routes import router
from utils import get_password_hash

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Authentication Service",
    version="1.0.0",
    description="JWT-based authentication service"
)

# Include routes
app.include_router(router)


def init_db():
    """Initialize database and create default admin user"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Create default admin user if not exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin)
            db.commit()
            logger.info("Created default admin user")
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    init_db()
    logger.info("Authentication service started")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
