FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent source
COPY src/ ./src/
COPY examples/ ./examples/

# Copy backend services (needed for LLM service import)
COPY ../backend/src/services/ ./backend_services/

ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main.py"]
