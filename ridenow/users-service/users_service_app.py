from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# -----------------------------
# Database setup (SQLite locale)
# -----------------------------
DATABASE_URL = "sqlite:///./data/users.db"  # fichier users.db créé dans ce dossier

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    zone = Column(String, nullable=False)
    available = Column(Boolean, default=True)


# Crée les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

# -----------------------------
# Schémas Pydantic
# -----------------------------
class DriverCreate(BaseModel):
    name: str
    zone: str
    available: bool = True


class DriverUpdateAvailability(BaseModel):
    available: bool


class DriverRead(BaseModel):
    id: int
    name: str
    zone: str
    available: bool

    class Config:
        orm_mode = True  # permet de retourner des objets SQLAlchemy


# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(
    title="Users Service - RideNow",
    description="Service de gestion des chauffeurs pour RideNow",
    version="1.0.0",
)


# Dépendance : session DB par requête
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Endpoints
# -----------------------------

@app.get("/health", tags=["health"])
def health_check():
    """
    Simple endpoint pour vérifier que le service est UP.
    """
    return {"status": "ok", "service": "users"}


@app.post("/drivers", response_model=DriverRead, tags=["drivers"])
def create_driver(driver_in: DriverCreate, db: Session = Depends(get_db)):
    """
    Créer un chauffeur.
    Utilisable pour initialiser la base et pour des tests.
    """
    print(f"[Users] Creating driver {driver_in.name} in zone {driver_in.zone}")
    driver = Driver(
        name=driver_in.name,
        zone=driver_in.zone,
        available=driver_in.available,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    print(f"[Users] Driver created with id={driver.id}")
    return driver


@app.get("/drivers", response_model=List[DriverRead], tags=["drivers"])
def list_drivers(
    available: Optional[bool] = Query(default=None),
    zone: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Lister les chauffeurs.
    Filtres possibles :
    - /drivers?available=true
    - /drivers?available=true&zone=A
    """
    print(f"[Users] Listing drivers with filters available={available}, zone={zone}")
    query = db.query(Driver)

    if available is not None:
        query = query.filter(Driver.available == available)
    if zone is not None:
        query = query.filter(Driver.zone == zone)

    drivers = query.all()
    print(f"[Users] Returned {len(drivers)} drivers")
    return drivers


@app.get("/drivers/{driver_id}", response_model=DriverRead, tags=["drivers"])
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """
    Récupérer un chauffeur par id.
    Utile pour le debug et la démo.
    """
    print(f"[Users] Fetching driver id={driver_id}")
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        print(f"[Users] Driver id={driver_id} not found")
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@app.patch("/drivers/{driver_id}/availability", response_model=DriverRead, tags=["drivers"])
def update_driver_availability(
    driver_id: int,
    payload: DriverUpdateAvailability,
    db: Session = Depends(get_db),
):
    """
    Met à jour la disponibilité d’un chauffeur.
    Le service Ride utilisera ça pour marquer un chauffeur comme occupé/libre.
    """
    print(f"[Users] Updating availability for driver id={driver_id} -> {payload.available}")
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        print(f"[Users] Driver id={driver_id} not found for availability update")
        raise HTTPException(status_code=404, detail="Driver not found")

    driver.available = payload.available
    db.commit()
    db.refresh(driver)
    print(f"[Users] Driver id={driver.id} availability updated to {driver.available}")
    return driver
