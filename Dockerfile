# ---------- Étape 1 : compiler le frontend ----------
FROM node:22-slim AS front
WORKDIR /front

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
ARG VITE_REYO_API_URL=/api
RUN npm run build

# ---------- Étape 2 : API + fichiers statiques ----------
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY --from=front /front/dist ./static

RUN useradd -m app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

CMD ["uvicorn", "reyo.api.main:app", "--host", "0.0.0.0", "--port", "8000"]