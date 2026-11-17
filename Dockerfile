# ---------- Étape 1 : compiler le frontend ----------
FROM node:22-slim AS front
WORKDIR /front

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# Le backend expose toutes ses routes sous /api : la base doit rester un chemin relatif.
ARG VITE_REYO_API_URL=/api
ENV VITE_REYO_API_URL=${VITE_REYO_API_URL}
RUN npm run build
# Le build SPA (tanstackStart.spa dans vite.config.ts) produit une coquille statique.
# StaticFiles sert index.html sur "/" : c'est le point d'entrée de l'application.
RUN cp .output/public/_shell.html .output/public/index.html

# ---------- Étape 2 : API + fichiers statiques ----------
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
# main.py monte ./static sur "/" quand le dossier existe (ci-dessous le front compilé).
COPY --from=front /front/.output/public ./static

RUN useradd -m app
USER app

EXPOSE 8000

# /health vit hors du préfixe /api, exactement comme la route déclarée dans main.py.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "reyo.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
