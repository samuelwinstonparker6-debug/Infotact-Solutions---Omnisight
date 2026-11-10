# OmniSight FastAPI + Playwright Backend Container
FROM python:3.11-slim

WORKDIR /app

# Install native build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser and OS dependencies
RUN playwright install chromium
RUN playwright install-deps

# Copy application source
COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
