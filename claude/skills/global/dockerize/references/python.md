# Reference implementation: Python

Covers Flask, Django, FastAPI — same stage shape, different start command and healthcheck path. Confirm the actual framework and entry point from the scan (step 1) before filling in the placeholders below.

**Multi-stage Dockerfile** — venv built once, copied into a clean runner, no compiler/build tools in the final image:

```dockerfile
# ---- deps: install dependencies into an isolated venv ----
FROM python:3.12-slim AS deps
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- dev: deps only — source is bind-mounted at runtime, never baked in ----
FROM deps AS dev
EXPOSE 8000

# ---- runner: venv + source, no build tools ----
FROM python:3.12-slim AS runner
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"

RUN groupadd --system app && useradd --system --gid app app

COPY --from=deps /opt/venv /opt/venv
COPY --chown=app:app . .

USER app
EXPOSE 8000
# Placeholder — replace with the real entry point:
#   Flask/FastAPI (gunicorn):  gunicorn --bind 0.0.0.0:8000 wsgi:app
#   FastAPI (uvicorn):         uvicorn app.main:app --host 0.0.0.0 --port 8000
#   Django:                    gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]
```

If the project uses Poetry or `pyproject.toml` instead of `requirements.txt`, swap the deps stage's install step accordingly (`pip install poetry && poetry export -f requirements.txt | pip install -r /dev/stdin`, or `pip install .` if the project itself is packaged) — keep the venv-then-copy shape, don't install directly into the system Python.

**`.dockerignore`**:

```
__pycache__
*.pyc
.venv
venv
.git
*.md
.env*
```

**`docker-compose.yml`** (base):

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: <app>:latest
    container_name: <app>
    ports:
      - "8000:8000"
```

**`docker-compose.override.yml`** (dev — bind mounts, hot reload):

```yaml
services:
  app:
    build:
      target: dev
    image: <app>:dev
    volumes:
      - .:/app
    command: >
      sh -c "
      python manage.py runserver 0.0.0.0:8000
      "
```

Replace the dev command with whatever the framework's own reload mode is: Django's `runserver` reloads by default; Flask needs `flask run --host=0.0.0.0 --debug` (or `--reload`); FastAPI/uvicorn needs `uvicorn app.main:app --host 0.0.0.0 --reload`. Unlike the Node case, the venv lives outside `/app` (`/opt/venv`), so a bind mount over `/app` doesn't shadow it — no anonymous-volume exclusion needed, *unless* the project keeps an in-project venv (Poetry's `virtualenvs.in-project`), in which case exclude that path the same way Node excludes `node_modules`.

**`docker-compose.prod.yml`** (prod overlay):

```yaml
services:
  app:
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

`python:3.12-slim` ships neither `curl` nor `wget` — a healthcheck written against either will silently fail to even run the check, not just fail the check. Use Python itself (shown above) to avoid adding a package just for this, or explicitly `apt-get install -y curl` in the runner stage if the app needs curl for other reasons anyway. Confirm the actual health path exists (`/health`, `/`, `/-/ready`) — don't assume.

**Migrations**: Django — `python manage.py migrate`; Flask-Migrate — `flask db upgrade`; SQLAlchemy/Alembic (FastAPI) — `alembic upgrade head`. Same auto-vs-manual choice as any other stack (see main SKILL.md step 3).
