# Reference implementation: Node / Next.js

This pattern is proven (built and run across several real iterations, not theoretical). Use it as the template for a Node/Next.js target; adapt the specifics for other Node frameworks (Express, Fastify, NestJS — same stage shape, different build/start commands and port).

**Multi-stage Dockerfile** — four stages, each with one job:

```dockerfile
# ---- deps: install dependencies only ----
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

# ---- dev: deps only — source is bind-mounted at runtime, never baked in ----
FROM deps AS dev
EXPOSE 3000

# ---- builder: build the app using those dependencies ----
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- runner: only the standalone output actually needed to run ----
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Docker sets HOSTNAME to the container ID; Next.js's standalone server
# binds to it if set, so it must be pinned to 0.0.0.0 or it only listens
# on the container's internal IP, not localhost.
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

Requires `output: "standalone"` in `next.config`. If a build-time-only public env var is needed (`NEXT_PUBLIC_*`, inlined into the client bundle), pass it as a Dockerfile `ARG`/`ENV` pair supplied by Compose — `.dockerignore` should exclude `.env*` from the build context (keeps secrets out of image layers), which also means Next.js's own automatic `.env` loading won't see it at build time; that gap is exactly what the explicit `ARG` bridges.

If the app uses an ORM with a generate/postinstall step that reads a connection string at *build* time (e.g. Prisma's `postinstall`), set a placeholder value for that var before the install step — build time never actually opens a connection, only the real runtime value (from Compose) matters.

**`.dockerignore`**:

```
node_modules
.next
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
      - "3000:3000"
```

Always set `container_name` — makes the container findable in Docker Desktop / `docker ps` instead of an auto-generated name.

**`docker-compose.override.yml`** (dev — bind mounts, hot reload):

```yaml
services:
  app:
    build:
      target: dev
    image: <app>:dev
    volumes:
      - .:/app
      - /app/node_modules
      - /app/.next
    environment:
      - HOSTNAME=0.0.0.0
    command: sh -c "npm run dev -- --hostname 0.0.0.0"
```

The `/app/node_modules` and `/app/.next` entries are anonymous volumes that shadow the host bind mount for just those two paths — without them the host's `node_modules` (or lack thereof, if installed only in-container) overwrites the container's, and `.next`'s build cache gets bind-mounted into a directory whose permissions/format don't match. This is the single most common breakage in a naive dev Compose setup — don't skip it.

**`docker-compose.prod.yml`** (prod overlay — applied on top of the base with `-f docker-compose.yml -f docker-compose.prod.yml`):

```yaml
services:
  app:
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:3000/"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
```

Use `127.0.0.1`, not `localhost` — in a minimal/Alpine image, `localhost` can resolve to `::1` first and fail if the app isn't also listening on IPv6.

Non-root user syntax above is Alpine's (`addgroup`/`adduser --system`). If the base image is Debian-derived instead (`node:22-slim`), the equivalent is `groupadd --system` / `useradd --system`.

**Dev / live-edit, Local-only variant** (tier 3 without Compose base — see SKILL.md step 2's tier 3 Local-only case):

```bash
docker run -d --name <app>-dev -p 3000:3000 \
  -v "$(pwd):/app" \
  -v /app/node_modules \
  -v /app/.next \
  <app>:dev \
  npm run dev -- --hostname 0.0.0.0
```

Same masking rule as the Compose override above, translated to `-v` flags: the `-v /app/node_modules` and `-v /app/.next` anonymous volumes must come *after* the `-v "$(pwd):/app"` bind mount and target the same two paths, or the host's `node_modules` (missing, or built for the wrong OS/arch) shadows the image's own install and the app breaks or runs stale/host packages instead of the image's. Build the `dev` target first (`docker build --target dev -t <app>:dev .`) — this variant still needs the image built once, only the source itself skips rebuild on edit.
