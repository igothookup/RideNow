FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy pydantic requests

# Copier le code du service
COPY . /app

# Lancer le service Users
CMD ["uvicorn", "users_service_app:app", "--host", "0.0.0.0", "--port", "8001"]
