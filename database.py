import os
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ Configurable database URL with fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./maize_yield.db")

# ✅ Enhanced engine creation with Render compatibility
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
    
    # Ensure directory exists for SQLite file
    if not DATABASE_URL.startswith("sqlite:////tmp"):
        db_path = DATABASE_URL.split("///")[-1]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
else:
    # Configuration for other databases (PostgreSQL, MySQL, etc.)
    engine = create_engine(DATABASE_URL)

# ✅ Your original Base declaration
Base = declarative_base()

# ✅ Your complete original Prediction model (unchanged)
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    Soil_Type = Column(String, nullable=False)
    pH = Column(Float, nullable=False)
    Seed_Variety = Column(String, nullable=False)
    Rainfall_mm = Column(Float, nullable=False)
    Temperature_C = Column(Float, nullable=False)
    Humidity_percent = Column(Float, nullable=False)
    Planting_Date = Column(String, nullable=False)
    Fertilizer_Type = Column(String, nullable=False)
    Predicted_Yield = Column(Float, nullable=False)
    Confidence_Range = Column(String, nullable=False)
    Category = Column(String, nullable=False)
    Recommendation = Column(String, nullable=False)

# ✅ Your original table creation
Base.metadata.create_all(bind=engine)

# ✅ Your original session configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Added get_db() dependency (compatible with FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()