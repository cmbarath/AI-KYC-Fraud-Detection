from backend.app.database import engine, Base
import backend.app.models  # Ensures all models are registered on Base

def init_database():
    """Initializes the SQLite database schema by creating all tables if not present."""
    print("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")

if __name__ == "__main__":
    init_database()
