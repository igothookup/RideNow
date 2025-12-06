# RideNow - Microservices Ride-Sharing Platform

A microservices-based ride-sharing application built with FastAPI, demonstrating distributed system architecture with independent services for users, pricing, payment processing, and ride management.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Services](#running-the-services)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Service Communication Flow](#service-communication-flow)
- [Testing](#testing)

## 🎯 Overview

RideNow is a microservices-based ride-sharing platform that separates concerns into independent services:
- **Users Service** (Port 8001): Manages drivers and their availability
- **Pricing Service** (Port 8002): Handles zone-based pricing rules
- **Payment Service** (Port 8003): Payment authorization and capture
- **Ride Service** (Port 8004): Orchestrates ride booking by coordinating with other services

Each service operates independently with its own database and API endpoints, communicating via HTTP REST APIs.

## 🏗️ Architecture

```
RideNow/
├── users-service/      # Driver management (Port 8001)
├── pricing-service/    # Pricing rules (Port 8002)
├── payment-service/    # Payment processing (Port 8003)
└── ride-service/       # Ride orchestration (Port 8004)
```

### Service Communication
- Services communicate via REST APIs
- Each service has its own SQLite database
- Services can be scaled independently
- Health check endpoints available for monitoring
- Ride Service orchestrates the booking flow by calling other services

## 🔧 Prerequisites

- **Python 3.10+** (tested with Python 3.13.1)
- **pip** (Python package manager)
- **Virtual environment** (recommended)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Tp3
```

### 2. Create and Activate Virtual Environment

**Windows:**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy pydantic
```

Or create a `requirements.txt` file:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
```

Then install:
```bash
pip install -r requirements.txt
```

## 🚀 Running the Services

### Users Service (Port 8001)

Navigate to the users service directory and start the server:

```bash
cd ridenow/users-service
uvicorn users_service_app:app --reload --port 8001
```

**Swagger Documentation:** http://localhost:8001/docs

**Health Check:** http://localhost:8001/health

### Pricing Service (Port 8002)

Navigate to the pricing service directory and start the server:

```bash
cd ridenow/pricing-service
uvicorn pricing_service_app:app --reload --port 8002
```

**Swagger Documentation:** http://localhost:8002/docs

**Health Check:** http://localhost:8002/health

### Payment Service (Port 8003)

Navigate to the payment service directory and start the server:

```bash
cd ridenow/payment-service
uvicorn payment_service_app:app --reload --port 8003
```

**Swagger Documentation:** http://localhost:8003/docs

**Health Check:** http://localhost:8003/health

### Ride Service (Port 8004)

Navigate to the ride service directory and start the server:

```bash
cd ridenow/ride-service
uvicorn ride_service_app:app --reload --port 8004
```

**Swagger Documentation:** http://localhost:8004/docs

**Health Check:** http://localhost:8004/health

### Running Multiple Services

Open separate terminal windows/tabs for each service, or use a process manager like `pm2` or `supervisor`.

**Note:** The Ride Service requires all other services to be running, as it orchestrates the booking flow.

## 📚 API Documentation

### Users Service API

#### Health Check
- **GET** `/health`
  - Returns service status

#### Driver Management
- **POST** `/drivers`
  - Create a new driver
  - Request body: `{ "name": "string", "zone": "string", "available": boolean }`
  
- **GET** `/drivers`
  - List all drivers
  - Query parameters:
    - `available` (optional): Filter by availability (true/false)
    - `zone` (optional): Filter by zone
  
- **GET** `/drivers/{driver_id}`
  - Get driver by ID
  
- **PATCH** `/drivers/{driver_id}/availability`
  - Update driver availability
  - Request body: `{ "available": boolean }`

**Example:**
```bash
# Create a driver
curl -X POST "http://localhost:8001/drivers" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "zone": "A", "available": true}'

# List available drivers in zone A
curl "http://localhost:8001/drivers?available=true&zone=A"
```

### Pricing Service API

#### Health Check
- **GET** `/health`
  - Returns service status

#### Pricing Management
- **POST** `/prices`
  - Create a pricing rule
  - Request body: `{ "from_zone": "string", "to_zone": "string", "amount": float }`
  
- **GET** `/price?from={zone}&to={zone}`
  - Get price for a route
  - Query parameters:
    - `from`: Origin zone (required)
    - `to`: Destination zone (required)

**Example:**
```bash
# Create a pricing rule
curl -X POST "http://localhost:8002/prices" \
  -H "Content-Type: application/json" \
  -d '{"from_zone": "A", "to_zone": "B", "amount": 12.50}'

# Get price for route A to B
curl "http://localhost:8002/price?from=A&to=B"
```

### Payment Service API

#### Health Check
- **GET** `/health`
  - Returns service status

#### Payment Management
- **POST** `/payments/authorize`
  - Authorize a payment for a ride
  - Request body: `{ "ride_id": int, "amount": float, "currency": "CAD" }`
  - Returns: `{ "payment_id": int, "status": "AUTHORIZED" }`
  
- **POST** `/payments/capture`
  - Capture a previously authorized payment
  - Request body: `{ "payment_id": int }`
  - Returns: `{ "payment_id": int, "status": "CAPTURED" }`
  
- **GET** `/payments/{payment_id}`
  - Get payment details by ID

**Example:**
```bash
# Authorize a payment
curl -X POST "http://localhost:8003/payments/authorize" \
  -H "Content-Type: application/json" \
  -d '{"ride_id": 1, "amount": 12.50, "currency": "CAD"}'

# Capture a payment
curl -X POST "http://localhost:8003/payments/capture" \
  -H "Content-Type: application/json" \
  -d '{"payment_id": 1}'
```

### Ride Service API

#### Health Check
- **GET** `/health`
  - Returns service status

#### Ride Management
- **POST** `/rides`
  - Create a new ride request
  - This endpoint orchestrates the entire booking flow:
    1. Finds an available driver in the requested zone
    2. Gets the price for the route
    3. Creates the ride record
    4. Authorizes payment
  - Request body: `{ "passenger_name": "string", "from_zone": "string", "to_zone": "string" }`
  - Returns: Complete ride details with driver, amount, and payment information
  
- **GET** `/rides/{ride_id}`
  - Get ride details by ID

**Example:**
```bash
# Create a ride (requires all other services to be running)
curl -X POST "http://localhost:8004/rides" \
  -H "Content-Type: application/json" \
  -d '{"passenger_name": "Alice", "from_zone": "A", "to_zone": "B"}'
```

## 📁 Project Structure

```
Tp3/
├── README.md
├── docker-compose.yml          # Docker configuration
├── .gitignore                  # Git ignore rules
├── ridenow/
│   ├── users-service/
│   │   ├── users_service_app.py    # Users service application
│   │   └── users.db                 # SQLite database (auto-created)
│   ├── pricing-service/
│   │   ├── pricing_service_app.py  # Pricing service application
│   │   └── pricing.db              # SQLite database (auto-created)
│   ├── payment-service/
│   │   ├── payment_service_app.py  # Payment service application
│   │   └── payment.db              # SQLite database (auto-created)
│   └── ride-service/
│       ├── ride_service_app.py     # Ride orchestration service
│       └── rides.db                # SQLite database (auto-created)
└── .venv/                          # Virtual environment (not in git)
```

## 🛠️ Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **Pydantic**: Data validation using Python type annotations
- **SQLite**: Lightweight database for each service

## 🔄 Service Communication Flow

When a ride is requested through the Ride Service, the following orchestration occurs:

1. **Ride Request** → `POST /rides` to Ride Service
2. **Find Driver** → Ride Service calls `GET /drivers?available=true&zone={zone}` on Users Service
3. **Get Price** → Ride Service calls `GET /price?from={zone}&to={zone}` on Pricing Service
4. **Create Ride** → Ride Service creates ride record in its database
5. **Authorize Payment** → Ride Service calls `POST /payments/authorize` on Payment Service
6. **Return Ride** → Ride Service returns complete ride details with driver, price, and payment info

This demonstrates a typical microservices orchestration pattern where one service coordinates multiple others to complete a business transaction.

## 🧪 Testing

### Manual Testing

1. **Start all services:**
   ```bash
   # Terminal 1 - Users Service
   cd ridenow/users-service
   uvicorn users_service_app:app --reload --port 8001
   
   # Terminal 2 - Pricing Service
   cd ridenow/pricing-service
   uvicorn pricing_service_app:app --reload --port 8002
   
   # Terminal 3 - Payment Service
   cd ridenow/payment-service
   uvicorn payment_service_app:app --reload --port 8003
   
   # Terminal 4 - Ride Service
   cd ridenow/ride-service
   uvicorn ride_service_app:app --reload --port 8004
   ```

2. **Setup Test Data:**
   ```bash
   # Create a driver in zone A
   curl -X POST "http://localhost:8001/drivers" -H "Content-Type: application/json" -d '{"name": "John Doe", "zone": "A", "available": true}'
   
   # Create a pricing rule for A to B
   curl -X POST "http://localhost:8002/prices" -H "Content-Type: application/json" -d '{"from_zone": "A", "to_zone": "B", "amount": 12.50}'
      ```

3. **Test Complete Ride Flow:**
   ```bash
   # Create a ride (this orchestrates all services) 
   curl -X POST "http://localhost:8004/rides" -H "Content-Type: application/json" -d '{"passenger_name": "Alice", "from_zone": A", "to_zone": "B"}'
   ```

4. **Interactive API Documentation:**
   - Users Service: http://localhost:8001/docs
   - Pricing Service: http://localhost:8002/docs
   - Payment Service: http://localhost:8003/docs
   - Ride Service: http://localhost:8004/docs

## 📝 Notes

- Databases are automatically created on first service startup
- Each service uses SQLite for simplicity (can be upgraded to PostgreSQL/MySQL)
- Services run independently and can be deployed separately
- The `--reload` flag enables auto-reload during development

## 🤝 Contributing

This is a learning project demonstrating microservices architecture. Potential enhancements:
- Docker containerization (docker-compose.yml exists but needs configuration)
- Database migrations (Alembic)
- Unit and integration tests
- API gateway for unified entry point
- Service discovery (Consul, Eureka)
- Message queue for async communication (RabbitMQ, Kafka)
- Distributed tracing (Jaeger, Zipkin)
- Circuit breakers for resilience
- Rate limiting
- Authentication and authorization

## 📄 License

This project is for educational purposes.

---

**Built with ❤️ using FastAPI and Python**
