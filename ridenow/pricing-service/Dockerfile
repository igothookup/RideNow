FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pydantic requests

COPY . /app

CMD ["uvicorn", "pricing_service_app:app", "--host", "0.0.0.0", "--port", "8002"]
