# ── Stage 1: Build React Frontend ────────────────────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install --silent

COPY frontend/ ./

RUN npm run build

# ── Stage 2: Python Backend + Serve Frontend ──────────────────────────────────
FROM python:3.10-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY api.py .
COPY features.py .
COPY insights_engine.py .
COPY auth/ ./auth/
COPY db/ ./db/

# Copy React build from Stage 1
COPY --from=frontend-build /app/frontend/build ./frontend/build

# Install serve for React static files
RUN pip install --no-cache-dir aiofiles

# Environment
ENV GROQ_API_KEY=""
ENV GROQ_MODEL="llama-3.3-70b-versatile"
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000
EXPOSE 3000

# Start script
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
