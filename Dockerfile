FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
COPY --from=frontend /build/dist /app/frontend/dist
RUN python -m pip install --no-cache-dir -e . && useradd --create-home --uid 10001 dataqa
USER dataqa
EXPOSE 8000
CMD ["sh", "-c", "python -m backend.app.bootstrap && exec python -m uvicorn backend.app.api:app --host 0.0.0.0 --port 8000 --workers 1"]
