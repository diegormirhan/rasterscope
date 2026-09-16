FROM node:22-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
# styles.css imports ../../tokens.css, so this stage has to mirror the repository
# layout: the token file sits beside the frontend directory, not inside it. Copying
# only frontend/ builds an image whose CSS cannot resolve.
COPY tokens.css /build/tokens.css
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN pip install --no-cache-dir .

COPY config.yaml ./
COPY artifacts/ artifacts/
COPY --from=frontend-build /build/frontend/dist frontend/dist

# A platform that assigns the port (Render, Fly, Cloud Run) sets PORT; locally the
# default above applies. EXPOSE is documentation only and cannot read it.
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ['PORT'] + '/api/health')"

# Shell form, because the exec form does not expand ${PORT}.
CMD ["sh", "-c", "exec uvicorn rasterscope.api.app:app --host 0.0.0.0 --port ${PORT}"]
