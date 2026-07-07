<div align="center">
  <img src="template-icon.svg" width="200" alt="Plausible CE Logo"/>
  <h1 align="center">Plausible Community Edition</h1>
  <p align="center">
    <strong>Privacy-friendly, open-source web analytics built for the modern web</strong>
  </p>
  <p align="center">
    <a href="https://railway.com/new/template/plausible-2">
      <img src="https://railway.app/button.svg" alt="Deploy on Railway" height="40"/>
    </a>
  </p>
  <br>
</div>

# Deploy and Host

Deploy **Plausible Community Edition** on Railway in minutes. Plausible is a lightweight, open-source web analytics platform that doesn't use cookies and is fully compliant with GDPR, CCPA, and PECR. This template sets up Plausible CE with ClickHouse for high-performance analytics storage and PostgreSQL for metadata.

## About Hosting

Plausible CE is the self-hosted version of [Plausible Analytics](https://plausible.io), a privacy-first alternative to Google Analytics. Unlike traditional analytics tools, Plausible:

- **No cookies required** — No cookie consent banners needed
- **GDPR/CCPA compliant** out of the box
- **Lightweight script** — < 1KB, loads instantly
- **ClickHouse-powered** — Handles millions of page views
- **27.4K+ GitHub stars** — Battle-tested by thousands

This Railway template deploys three components:

| Component | Purpose | Image |
|-----------|---------|-------|
| **Plausible CE** | Web analytics application | `ghcr.io/plausible/community-edition:v3.2.1` |
| **ClickHouse** | Column-oriented analytics database | `clickhouse/clickhouse-server:24.12-alpine` |
| **PostgreSQL** | Metadata and user data storage | Railway plugin |

## Why Deploy

- **Eliminate Google Analytics** — Own your analytics data completely
- **Privacy by default** — No tracking cookies, no personal data collection
- **Lightweight performance** — Tracking script is ~45KB gzipped
- **Infinite scalability** — ClickHouse handles billions of events
- **Real-time dashboards** — See visitor data as it comes in
- **Zero-config SEO** — Built-in sitemaps, canonical URLs, Open Graph

## Common Use Cases

- **SaaS Products** — Track feature usage and user behavior without third-party scripts
- **Content Websites** — Monitor traffic, top pages, and referral sources
- **E-commerce** — Analyze conversion funnels and traffic sources
- **Personal Blogs** — Simple, privacy-respecting visitor analytics
- **Enterprise Intranets** — Host behind your firewall for internal analytics

## Dependencies for Plausible

### Deployment Dependencies

- **Railway Account** — Sign up at [railway.app](https://railway.app)
- **PostgreSQL Plugin** — Added automatically via Railway's plugin system
- **Custom Domain** (recommended) — For production deployments

All services are containerized and deploy with a single click.

---

## Quick Start

### 1. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.com/new/template/plausible-2)

Click the button above. Railway will:
1. Create the Plausible CE service
2. Create the ClickHouse service
3. Add a PostgreSQL database plugin
4. Wire internal networking between services

### 2. Configure Environment Variables

Set these **required** variables in Railway dashboard:

| Variable | Description | How to Get |
|----------|-------------|------------|
| `BASE_URL` | Public URL of your Plausible instance | `https://your-app.up.railway.app` |
| `SECRET_KEY_BASE` | 64-byte random string for encryption | `openssl rand -base64 48` |
| `CLICKHOUSE_DATABASE_URL` | ClickHouse connection string | See networking section below |

> **Network Tip:** ClickHouse runs as a Railway companion service with auto-generated credentials (`CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`). The `CLICKHOUSE_DATABASE_URL` is automatically constructed using these credentials via Railway's variable references.

### 3. Access Your Instance

Once deployed, visit your `BASE_URL` and register the first user account.

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `BASE_URL` | Public URL (no trailing slash), e.g. `https://plausible.yourdomain.com` |
| `SECRET_KEY_BASE` | At least 64-byte random base64 string for cookie signing |
| `DATABASE_URL` | PostgreSQL connection string (auto-populated by Railway plugin) |
| `CLICKHOUSE_DATABASE_URL` | ClickHouse connection string (auto-constructed from companion ClickHouse service credentials) |

### Registration

| Variable | Description |
|----------|-------------|
| `DISABLE_REGISTRATION` | Set to `true` to prevent new user signups after initial setup |
| `ENABLE_EMAIL_VERIFICATION` | Set to `true` to require email verification |
| `TOTP_VAULT_KEY` | Key for encrypting TOTP two-factor secrets |

### Email (SMTP)

| Variable | Description |
|----------|-------------|
| `MAILER_ADAPTER` | Email adapter: `Bamboo.SMTPAdapter` (SMTP), `Bamboo.PostmarkAdapter`, etc. |
| `MAILER_EMAIL` | From email address for outgoing emails |
| `MAILER_NAME` | From name for outgoing emails |
| `SMTP_HOST_ADDR` | SMTP server address |
| `SMTP_HOST_PORT` | SMTP server port |
| `SMTP_USER_NAME` | SMTP username |
| `SMTP_USER_PWD` | SMTP password |
| `SMTP_HOST_SSL_ENABLED` | Set to `true` to enable SSL/TLS |

### Google Auth

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |

### IP Geolocation

| Variable | Description |
|----------|-------------|
| `IP_GEOLOCATION_DB` | Geolocation database: `city` (MaxMind City) |
| `MAXMIND_LICENSE_KEY` | MaxMind license key for GeoIP database downloads |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Railway Project                          │
│                                                              │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │   Plausible CE    │─────▶│    ClickHouse     │           │
│  │   (Elixir/Phoenix)│      │   (Analytics DB)  │          │
│  │   :8000           │      │   :8123/:9000     │           │
│  └────────┬──────────┘      └──────────────────┘            │
│           │                                                 │
│           ▼                                                 │
│  ┌──────────────────┐                                       │
│  │   PostgreSQL      │                                       │
│  │   (Railway Plugin)│                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

- **Plausible CE** — Main application server (Elixir/Phoenix)
- **ClickHouse** — Columnar analytics database for storing events
- **PostgreSQL** — Relational database for users, sites, and metadata

All internal communication happens over Railway's private network.

---

## Troubleshooting

### ClickHouse fails to start

ClickHouse requires **SSE 4.2** or **NEON** CPU instruction support. Most modern CPUs support this. If using an older/ARM instance:

1. Check Railway's region for CPU compatibility
2. Consider using an external ClickHouse Cloud service instead

### Connection refused to services

Services may need time to start. ClickHouse and PostgreSQL start in parallel:
- ClickHouse: ~30 seconds startup time
- PostgreSQL: ~10 seconds startup time
- Plausible CE: waits for both before starting

### Registration is open

Anyone who knows your URL can register. After creating your account:
1. Set `DISABLE_REGISTRATION=true` in Railway dashboard
2. Restart the Plausible service

### Health check fails

The health endpoint is at `/api/health`. Plausible CE takes 30-60 seconds to start on first deploy as it runs database migrations. This is normal.

---

## License

Plausible CE is licensed under [AGPL-3.0](https://github.com/plausible/analytics/blob/master/LICENSE.md).

---

## Resources

- [Plausible CE Wiki](https://github.com/plausible/community-edition/wiki)
- [Plausible CE Repository](https://github.com/plausible/community-edition)
- [Plausible Documentation](https://plausible.io/docs)
- [Railway Documentation](https://docs.railway.app)
