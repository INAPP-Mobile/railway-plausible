<div align="center">
  <img src="template-icon.svg" width="200" alt="Plausible CE Logo"/>
  <h1 align="center">Plausible Community Edition</h1>
  <p align="center"><strong>Privacy-friendly, open-source web analytics for the modern web</strong></p>
  <p align="center">
    <a href="https://railway.com/new/template/plausible-1"><img src="https://railway.app/button.svg" alt="Deploy on Railway" height="40"/></a>
  </p>
  <br/>
</div>

# Deploy and Host

**Plausible Community Edition** on Railway. Lightweight, open-source web analytics with no cookies, GDPR/CCPA/PECR compliant out of the box. This template deploys three sibling services so every marketplace deploy boots into a working state with no manual env-var hunting.

## About Plausible

- **No cookies required** — no consent banners
- **Lightweight script** — < 1 KB
- **ClickHouse-powered** — handles millions of page views
- **27.4K+ GitHub stars** — battle-tested at scale

## Services Deployed

| Service | Image | Volume Mount | Notes |
|---------|-------|--------------|-------|
| **Plausible CE** | `ghcr.io/plausible/community-edition:v3.2.1` | — | Elixir/Phoenix app on port 8000 |
| **ClickHouse** | `clickhouse/clickhouse-server:24.12-alpine` | `/var/lib/clickhouse` | Analytics event store |
| **PostgreSQL** | `postgres:16-alpine` (upstream) | `/var/lib/postgresql` (parent) | Metadata + users |

> **Why upstream `postgres:16-alpine` instead of the Railway `postgres-ssl:18` plugin?** The plugin forces PGDATA to match the volume mount path exactly. With the Railway volume mount default of `/var/lib/postgresql/data`, the volume's ext4 `lost+found/` directory ends up *inside* PGDATA — and `initdb` crashes with `directory exists but is not empty`. The sibling-service fix mounts the volume at the **parent** path `/var/lib/postgresql` with `PGDATA=/var/lib/postgresql/data`, so `lost+found/` lives at the volume root, outside PGDATA. See `postgres/.env.example` for the full rationale, or `.agents/skills/railway-deployment/references/plausible-ce-and-postgres-docker-patterns.md` § "Lost+Found Gotcha — Empirically Verified 2026-07-08".

## Why Deploy

- **Own your analytics** — eliminate Google Analytics
- **Privacy by default** — no tracking cookies, no fingerprinting
- **Real-time dashboards** — see visitors as they arrive
- **GDPR/CCPA compliant** out of the box

## Common Use Cases

SaaS analytics (no third-party scripts), content websites (monitor traffic + referrals), e-commerce conversion analytics, personal blogs, or behind-the-firewall internal analytics.

## Quick Start

### 1. Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/new/template/plausible-1)

Railway creates all three sibling services in one click and wires internal networking. Wait ~30-60 seconds for Postgres initdb (~30s) and Plausible CE DB migrations (~60s on first boot).

### 2. Configure environment variables (if any)

The template ships with literal defaults that work out of the box. Most users won't need to touch anything. The variables you *can* rotate (and must keep in sync between services):

- `DATABASE_URL` (Plausible CE) — credentials match the Postgres sibling tile defaults
- `CLICKHOUSE_DATABASE_URL` (Plausible CE) — credentials match ClickHouse sibling tile defaults
- `BASE_URL` (Plausible CE) — defaults to `https://${{RAILWAY_PUBLIC_DOMAIN}}` (auto)
- `SECRET_KEY_BASE` (Plausible CE) — defaults to `${{secret(64)}}` (auto-generated)

If you rotate `POSTGRES_PASSWORD` or `CLICKHOUSE_PASSWORD` on their respective tiles, update the corresponding Plausible CE URL in the same change.

### 3. Register the first user

Visit `BASE_URL` (e.g. `https://plausible-ce-production-XXXX.up.railway.app`) and create your admin account. Then set `DISABLE_REGISTRATION=true` if you don't want public signups.

## Environment Variables

### Plausible CE (root)

| Variable | Default | Notes |
|----------|---------|-------|
| `BASE_URL` | `https://${{RAILWAY_PUBLIC_DOMAIN}}` | Auto — protocol prefix required by Plausible |
| `SECRET_KEY_BASE` | `${{secret(64)}}` | Auto — 64-char random |
| `DATABASE_URL` | `postgresql://postgres:postgres@postgres.railway.internal:5432/plausible` | Cookie signing secret |
| `CLICKHOUSE_DATABASE_URL` | `http://plausible:plausible2026@clickhouse.railway.internal:8123/plausible` | Must match ClickHouse tile creds |
| `DISABLE_REGISTRATION` | `false` | Flip to `true` after admin signup |
| `ENABLE_EMAIL_VERIFICATION` | `false` | Optional |
| `TOTP_VAULT_KEY` | (unset) | Required for 2FA |

### Postgres (`postgres/` sibling service)

| Variable | Default | Notes |
|----------|---------|-------|
| `POSTGRES_USER` | `postgres` | Matches DATABASE_URL user portion |
| `POSTGRES_PASSWORD` | `postgres` | Must match DATABASE_URL password part |
| `POSTGRES_DB` | `plausible` | Initial DB; matches DATABASE_URL path component |
| `PGDATA` | `/var/lib/postgresql/data` | Subpath of `/var/lib/postgresql` mount — sidesteps lost+found gotcha |
| `MAX_CONNECTIONS`, `SHARED_BUFFERS` | (unset) | Optional tuning |

### ClickHouse (`clickhouse/` sibling service)

| Variable | Default | Notes |
|----------|---------|-------|
| `CLICKHOUSE_USER` | `plausible` | Matches URL user portion |
| `CLICKHOUSE_PASSWORD` | `plausible2026` | Matches URL password part |
| `CLICKHOUSE_DB` | `plausible` | Matches URL path component |

### Optional (SMTP, Google Auth, GeoIP)

SMTP, Google OAuth, and MaxMind GeoIP are unchanged from prior templates — see `.env.example` for the full list. Defaults auto-skip these unless you uncomment them.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Railway Project                          │
│                                                              │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │   Plausible CE    │─────▶│    ClickHouse     │           │
│  │   :8000           │      │   :8123:9000      │          │
│  └────────┬──────────┘      └──────────────────┘            │
│           ▼                                                  │
│  ┌──────────────────┐                                        │
│  │   PostgreSQL      │  Image: postgres:16-alpine (upstream)│
│  │   (sibling)       │  Volume mount: /var/lib/postgresql   │
│  │                   │  PGDATA: /var/lib/postgresql/data     │
│  │                   │  → lost+found/ stays OUTSIDE PGDATA   │
│  └──────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

All three services communicate via Railway's private network (`postgres.railway.internal`, `clickhouse.railway.internal`).

## Troubleshooting

### Postgres crashes with `directory exists but is not empty`

Confirm the Volume widget on the Postgres tile is set to mount at `/var/lib/postgresql` (NOT `/var/lib/postgresql/data`). The latter traps `lost+found/` inside PGDATA. See `postgres/.env.example` for the geometry explanation.

### Volume widget settings don't survive marketplace deploy

Railway's UI widget for volumeMounts may not always serialize into the `serializedConfig.services.<id>.volumeMounts` block. If a fresh marketplace deploy lacks the postgres volume, verify in the template editor's root-level Raw JSON that the postgres service has `volumeMounts: { "/var/lib/postgresql": {...} }`. If it's missing, you can either (a) inject it manually in the root Raw JSON editor, or (b) switch to IaC (`.railway/railway.ts`) for durable volumeMounts encoding. Worst case, run `railway volume add --service <postgres-id> --mount-path /var/lib/postgresql` post-deploy.

### Connection refused Postgres on first deploy

Postgres initdb runs on first boot — allow ~30 seconds. Check `railway logs --service Postgres`.

### Plausible logs show ECONNREFUSED / cannot create schema_migrations

Postgres is still initializing (wait + refresh), OR Plausible CE's `DATABASE_URL` doesn't match the Postgres tile defaults (verify both via `railway variables --service <name> --kv`).

### Health endpoint returns 502

First deploy takes 60-90 seconds while both Postgres (`initdb`) and Plausible CE (`db migrate` + Elixir release boot) initialize. If 502 persists past 2 minutes, check Postgres logs first — most failures cascade from there.

### Registration stays open after admin signup

Set `DISABLE_REGISTRATION=true` on the Plausible CE tile and redeploy.

## License

Plausible CE is licensed under [AGPL-3.0](https://github.com/plausible/analytics/blob/master/LICENSE.md).

## Resources

- [Plausible CE Repository](https://github.com/plausible/community-edition)
- [Plausible CE Wiki](https://github.com/plausible/community-edition/wiki)
- [Plausible Documentation](https://plausible.io/docs)
- [Railway Documentation](https://docs.railway.app)
- Lost+Found gotcha reference: `.agents/skills/railway-deployment/references/plausible-ce-and-postgres-docker-patterns.md` § "Lost+Found Gotcha — Empirically Verified 2026-07-08"