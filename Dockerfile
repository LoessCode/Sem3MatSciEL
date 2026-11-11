# Stage 1: build the React frontend
FROM node:22-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime serving the API and the built frontend on :8000
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/ ./backend/
COPY data/ ./data/
RUN pip install --no-cache-dir ./backend
COPY --from=frontend /build/frontend/dist ./frontend/dist
ENV AIRFRAMESELECT_DATA_DIR=/app/data AIRFRAMESELECT_STATIC_DIR=/app/frontend/dist
EXPOSE 8000
CMD ["uvicorn", "airframeselect.api:app", "--host", "0.0.0.0", "--port", "8000"]
