from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# -----------------------------
# Database setup (SQLite locale)
# -----------------------------
DATABASE_URL = "sqlite:///./data/pricing.db"  # fichier pricing.db dans ce dossier

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    from_zone = Column(String, nullable=False)
    to_zone = Column(String, nullable=False)
    amount = Column(Float, nullable=False)


# Crée les tables si elles n'existent pas
Base.metadata.create_all(bind=engine)

# -----------------------------
# Schémas Pydantic
# -----------------------------
class PricingRuleCreate(BaseModel):
    from_zone: str
    to_zone: str
    amount: float


class PricingRuleRead(BaseModel):
    id: int
    from_zone: str
    to_zone: str
    amount: float

    class Config:
        orm_mode = True


class PriceResponse(BaseModel):
    from_zone: str
    to_zone: str
    amount: float
    currency: str = "CAD"


# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(
    title="Pricing Service - RideNow",
    description="Service de tarification par zones pour RideNow",
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
    """
    Vérifie que le service de pricing est UP.
    """
    return {"status": "ok", "service": "pricing"}


@app.post("/prices", response_model=PricingRuleRead, tags=["pricing"])
def create_pricing_rule(rule_in: PricingRuleCreate, db: Session = Depends(get_db)):
    """
    Créer une règle de prix pour un trajet from_zone -> to_zone.
    Utile pour initialiser la base (ex: A->B = 12.5).
    """
    from_zone = rule_in.from_zone.upper()
    to_zone = rule_in.to_zone.upper()

    # On pourrait vérifier s'il existe déjà une règle pour cette route
    existing = (
        db.query(PricingRule)
        .filter(
            PricingRule.from_zone == from_zone,
            PricingRule.to_zone == to_zone
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Pricing rule for {from_zone} -> {to_zone} already exists (id={existing.id})",
        )

    rule = PricingRule(
        from_zone=from_zone,
        to_zone=to_zone,
        amount=rule_in.amount,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@app.get("/price", response_model=PriceResponse, tags=["pricing"])
def get_price(
    from_zone: str = Query(..., alias="from"),
    to_zone: str = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    """
    Retourne le prix pour un trajet from_zone -> to_zone.
    Exemple : GET /price?from=A&to=B
    """
    from_zone = from_zone.upper()
    to_zone = to_zone.upper()

    rule = (
        db.query(PricingRule)
        .filter(
            PricingRule.from_zone == from_zone,
            PricingRule.to_zone == to_zone,
        )
        .first()
    )

    if not rule:
        raise HTTPException(
            status_code=404,
            detail=f"No pricing rule for route {from_zone} -> {to_zone}",
        )

    return PriceResponse(
        from_zone=from_zone,
        to_zone=to_zone,
        amount=rule.amount,
        currency="CAD",
    )
