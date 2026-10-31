# Reference implementation: plain static files

No framework, no build step, no package manifest — just HTML/CSS/JS served as-is. The Dockerfile itself is trivial; the real decision is which base image, and the gotcha is who it runs as.

**Base image choice** — surface sizes (`docker manifest inspect`, per step 3's base-image-size rule) and pick with the user rather than defaulting silently if leanness or non-root matters to them:

| Image | Compressed size (~) | Runs as | Notes |
|---|---|---|---|
| `nginx:<pinned>-alpine` | ~8-10MB | root (default) | Smallest, most standard; needs `nginx-unprivileged` swap for non-root without extra config. |
| `nginxinc/nginx-unprivileged:<pinned>-alpine` | ~8-10MB | non-root by default | Same nginx, listens on 8080 instead of 80 (unprivileged ports only) — adjust the port mapping accordingly. |
| `caddy:<pinned>-alpine` | ~30-40MB | root (default) | Larger, but automatic HTTPS and a much simpler config file if that's ever relevant beyond local/dev use. |

Default to `nginx:<pinned>-alpine` unless the user has already asked for non-root hardening (pick `nginx-unprivileged` then) or has a reason to want Caddy.

**Dockerfile**:

```dockerfile
FROM nginx:1.31-alpine
COPY . /usr/share/nginx/html
EXPOSE 80
```

Pin the tag (`nginx:1.31-alpine`, not `nginx:alpine`) so the base doesn't silently drift on a future rebuild.

**`.dockerignore`**:

```
.git
.dockerignore
Dockerfile
README.md
DOCKER.md
```

**Non-root gotcha**: the stock `nginx` image runs its worker process as root inside the container by default (it drops privileges for the worker, but the master process and initial bind still start as root) — if "Prod-hardened" scope was selected, swap to `nginxinc/nginx-unprivileged` rather than trying to retrofit `USER` onto the stock image, which fights nginx's own privilege-drop logic and port-80 bind requirement.

**SPA fallback**: if the project is a single-page app (client-side routing) rather than literal standalone HTML, the stock nginx config will 404 on any deep-linked route. Needs a custom `nginx.conf` fragment with `try_files $uri /index.html;`, copied in alongside the static files. Not needed for genuinely static multi-page sites — confirm which case this actually is before adding it.

**Compose base** (if tier 2 selected):

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: <app>:latest
    container_name: <app>
    ports:
      - "80:80"
```

**Dev / live-edit, Local-only variant** (tier 3 without Compose — see SKILL.md step 2's tier 3 Local-only case):

```bash
docker run -d --name <app>-dev -p 6767:80 \
  -v "$(pwd)/index.html:/usr/share/nginx/html/index.html:ro" \
  <app>:latest
```

Mount read-only (`:ro`) — the container never needs to write back to the host copy. Editing `index.html` on the host is reflected immediately, no rebuild — see SKILL.md step 5 for the cwd and browser-cache caveats that belong in the generated `DOCKER.md` for this flow.
