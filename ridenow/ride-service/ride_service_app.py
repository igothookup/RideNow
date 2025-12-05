from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import requests

# -----------------------------------------------------
# DB locale SQLite (ride.db)
# -----------------------------------------------------
DATABASE_URL = "sqlite:///./data/rides.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    passenger_name = Column(String, nullable=False)
    from_zone = Column(String, nullable=False)
    to_zone = Column(String, nullable=False)
    driver_id = Column(Integer, nullable=True)
    amount = Column(Float, nullable=True)
    payment_id = Column(Integer, nullable=True)
    status = Column(String, default="REQUESTED")  # REQUESTED / ASSIGNED / ...


Base.metadata.create_all(bind=engine)

# -----------------------------------------------------
# Config — URLs des autres services
# -----------------------------------------------------
#USERS_URL = "http://localhost:8001"
#PRICING_URL = "http://localhost:8002"
#PAYMENT_URL = "http://localhost:8003"
USERS_URL = "http://users-service:8001"
PRICING_URL = "http://pricing-service:8002"
PAYMENT_URL = "http://payment-service:8003"


# -----------------------------------------------------
# Schemas Pydantic
# -----------------------------------------------------
class RideCreate(BaseModel):
    passenger_name: str
    from_zone: str
    to_zone: str


class RideRead(BaseModel):
    id: int
    passenger_name: str
    from_zone: str
    to_zone: str
    driver_id: int
    amount: float
    payment_id: int
    status: str

    class Config:
        orm_mode = True


# -----------------------------------------------------
# App FastAPI
# -----------------------------------------------------
app = FastAPI(
    title="Ride Service - RideNow",
    description="Service d'orchestration des courses",
    version="1.0.0",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------
# Endpoints
# -----------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "service": "ride"}


@app.post("/rides", response_model=RideRead)
def create_ride(payload: RideCreate, db: Session = Depends(get_db)):
    print("[Ride] Creating ride request...")

    # 1. Trouver un chauffeur dispo
    print("[Ride] Fetching available drivers...")
    r = requests.get(
        f"{USERS_URL}/drivers",
        params={"available": True, "zone": payload.from_zone},
    )
    if r.status_code != 200:
        raise HTTPException(500, "Users service error")

    drivers = r.json()
    if not drivers:
        raise HTTPException(404, "No available driver in this zone")

    driver = drivers[0]
    driver_id = driver["id"]
    print(f"[Ride] Selected driver: {driver_id}")

    # 2. Récupérer le prix
    print("[Ride] Fetching price...")
    p = requests.get(
        f"{PRICING_URL}/price",
        params={"from": payload.from_zone, "to": payload.to_zone},
    )
    if p.status_code != 200:
        raise HTTPException(404, "No price for this route")

    price_data = p.json()
    amount = price_data["amount"]

    # 3. Créer la course en DB
    ride = Ride(
        passenger_name=payload.passenger_name,
        from_zone=payload.from_zone.upper(),
        to_zone=payload.to_zone.upper(),
        driver_id=driver_id,
        amount=amount,
        status="ASSIGNED",
    )
    db.add(ride)
    db.commit()
    db.refresh(ride)

    print(f"[Ride] Ride created with id {ride.id}")

    # 4. Autoriser le paiement
    print("[Ride] Authorizing payment...")
    pay = requests.post(
        f"{PAYMENT_URL}/payments/authorize",
        json={"ride_id": ride.id, "amount": amount, "currency": "CAD"},
    )
    if pay.status_code != 200:
        raise HTTPException(500, "Payment authorization failed")

    payment_data = pay.json()
    payment_id = payment_data["payment_id"]

    # 5. Mettre à jour le ride avec payment_id
    ride.payment_id = payment_id
    db.commit()
    db.refresh(ride)

    print("[Ride] Payment authorized.")

    return ride


@app.get("/rides/{ride_id}", response_model=RideRead)
def get_ride(ride_id: int, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(404, "Ride not found")
    return ride
