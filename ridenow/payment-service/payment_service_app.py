from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# -----------------------------
# DB SQLite locale
# -----------------------------
DATABASE_URL = "sqlite:///./data/payment.db"


engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)  # AUTHORIZED / CAPTURED / FAILED


Base.metadata.create_all(bind=engine)


# -----------------------------
# Schemas Pydantic
# -----------------------------
class PaymentAuthorizeRequest(BaseModel):
    ride_id: int
    amount: float
    currency: str = "CAD"


class PaymentAuthorizeResponse(BaseModel):
    payment_id: int
    status: str


class PaymentCaptureRequest(BaseModel):
    payment_id: int


class PaymentRead(BaseModel):
    id: int
    ride_id: int
    amount: float
    currency: str
    status: str

    class Config:
        orm_mode = True


# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(
    title="Payment Service - RideNow",
    description="Service de paiement simulé pour RideNow",
    version="1.0.0",
)


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
    return {"status": "ok", "service": "payment"}


@app.post("/payments/authorize", response_model=PaymentAuthorizeResponse, tags=["payments"])
def authorize_payment(
    payload: PaymentAuthorizeRequest,
    db: Session = Depends(get_db),
):
    """
    Simule l'autorisation d'un paiement.
    Le Ride Service appellera ceci après création de la course.
    """
    # Dans un vrai système on parlerait à un PSP (Stripe, etc.)
    # Ici on suppose que l'autorisation est toujours OK.
    payment = Payment(
        ride_id=payload.ride_id,
        amount=payload.amount,
        currency=payload.currency,
        status="AUTHORIZED",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return PaymentAuthorizeResponse(
        payment_id=payment.id,
        status=payment.status,
    )


@app.post("/payments/capture", response_model=PaymentAuthorizeResponse, tags=["payments"])
def capture_payment(
    payload: PaymentCaptureRequest,
    db: Session = Depends(get_db),
):
    """
    Simule la capture d'un paiement déjà autorisé.
    Le Ride Service appellera ceci quand la course passe à COMPLETED.
    """
    payment = db.query(Payment).filter(Payment.id == payload.payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status != "AUTHORIZED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot capture payment in status {payment.status}",
        )

    payment.status = "CAPTURED"
    db.commit()
    db.refresh(payment)

    return PaymentAuthorizeResponse(
        payment_id=payment.id,
        status=payment.status,
    )


@app.get("/payments/{payment_id}", response_model=PaymentRead, tags=["payments"])
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """
    Récupérer un paiement (utile pour debug et la démo).
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
