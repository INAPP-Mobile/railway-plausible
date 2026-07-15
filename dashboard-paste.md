# railway-plausible — Dashboard Paste Plan (Sibling-Service Postgres)

Target template code: **`f0NGX9`** (workspace-level draft; ID `766fb90f-9ead-45b5-b182-f6239b14afc1`).

## Dashboard navigation steps

1. Open <https://railway.com/dashboard/templates/766fb90f-9ead-45b5-b182-f6239b14afc1> in your browser.
2. **Postgres tile first** — configure the Volume mount widget (UI-only, cannot paste), then the Variables → Raw JSON tab.
3. **ClickHouse tile** — Variables → Raw JSON tab (paste block below).
4. **Plausible CE tile** — Variables → Raw JSON tab (paste block below).
5. After all three tiles saved, run the **Re-create draft command** at the bottom in your terminal to capture the updated service topology into a fresh template draft (AGENTS.md rule 3: do NOT auto-publish).

> Notes:
> - The per-service Raw JSON editor accepts only `{ "value": ..., "description": ... }` variables. Volume mounts, source image, healthcheck path, and icon are configured via UI widgets, not this JSON.
> - All three tiles use **literal credentials** (postgres/postgres, plausible/plausible2026, plausible DB). This is intentional: it eliminates the `${{Service.*}}` macro-resolution race that broke first-deploy auth in the postgres-ssl:18 plugin days. Rotate credentials in BOTH places (the credential tile + Plausible CE's DATABASE_URL) before going to production.

---

## 1. Postgres tile → Volume widget (configure BEFORE Variables)

In the Volume widget on the Postgres tile, create a volume with:

- **Mount path:** `/var/lib/postgresql` (parent path — NOT `/var/lib/postgresql/data`)
- **Size MB:** 5000 (5 GB)

> ⚠️ **CRITICAL:** The mount path MUST be `/var/lib/postgresql`. The `PGDATA` env var (set in step 2 below) is `/var/lib/postgresql/data` — a subpath of the mount. This geometry places the volume's ext4 `lost+found/` directory at `/var/lib/postgresql/lost+found` (outside `PGDATA`), letting initdb see PGDATA as an empty directory and proceed. Mounting at `/var/lib/postgresql/data` directly traps `lost+found/` inside PGDATA → initdb crashes with `error: directory "/var/lib/postgresql/data" exists but is not empty`. Every fresh marketplace deploy would fail if you take this shortcut.
>
> See `.agents/skills/railway-deployment/references/plausible-ce-and-postgres-docker-patterns.md` § "Lost+Found Gotcha — Empirically Verified 2026-07-08" for the full root cause.

---

## 2. Postgres tile → Variables → Raw JSON

```json
{
  "POSTGRES_USER": {
    "value": "postgres",
    "description": "Postgres superuser name. Must match the user portion of Plausible CE's DATABASE_URL."
  },
  "POSTGRES_PASSWORD": {
    "value": "postgres",
    "description": "Postgres password. Default literal 'postgres' chosen so marketplace first-time deploys authenticate against Plausible CE's literal DATABASE_URL out of the box. Rotate this in the dashboard AND update Plausible CE's DATABASE_URL if you change."
  },
  "POSTGRES_DB": {
    "value": "plausible",
    "description": "Initial database created on first boot. Must match the path component of Plausible CE's DATABASE_URL."
  },
  "PGDATA": {
    "value": "/var/lib/postgresql/data",
    "description": "Postgres data directory inside the volume. MUST remain a subpath of the Volume widget's /var/lib/postgresql mount — see section 1 for the lost+found geometry rationale."
  }
}
```

---

## 3. ClickHouse tile → Variables → Raw JSON

```json
{
  "CLICKHOUSE_DB": {
    "value": "plausible",
    "description": "ClickHouse database name for Plausible event storage."
  },
  "CLICKHOUSE_USER": {
    "value": "plausible",
    "description": "ClickHouse user. Default matches Plausible CE's CLICKHOUSE_DATABASE_URL."
  },
  "CLICKHOUSE_PASSWORD": {
    "value": "plausible2026",
    "description": "ClickHouse password. Default is a known literal for marketplace-safe deploys (no ${{secret(N)}} — secret() would generate a random value that conflicts with the literal URL on Plausible CE tile). Rotate this in dashboard before going to production, update Plausible CE's CLICKHOUSE_DATABASE_URL to match."
  }
}
```

---

## 4. Plausible CE tile → Variables → Raw JSON

```json
{
  "DATABASE_URL": {
    "value": "postgresql://postgres:postgres@postgres.railway.internal:5432/plausible",
    "description": "PostgreSQL connection URL to the sibling 'postgres' service. Literal credentials match Postgres tile defaults out of the box. If you rotate POSTGRES_PASSWORD on the Postgres tile, update this DATABASE_URL to match."
  },
  "BASE_URL": {
    "value": "https://${{RAILWAY_PUBLIC_DOMAIN}}",
    "description": "Public URL of deployed Plausible instance."
  },
  "SECRET_KEY_BASE": {
    "value": "${{secret(64)}}",
    "description": "64-byte random string for cookie signing. Auto-generated per deploy."
  },
  "CLICKHOUSE_DATABASE_URL": {
    "value": "http://plausible:plausible2026@clickhouse.railway.internal:8123/plausible",
    "description": "ClickHouse connection URL. Literal credentials match ClickHouse tile defaults. If you rotate CLICKHOUSE_PASSWORD on the ClickHouse tile, update this URL to match."
  },
  "DISABLE_REGISTRATION": {
    "value": "false",
    "description": "Set to true after creating your admin user to prevent public signups."
  },
  "ENABLE_EMAIL_VERIFICATION": {
    "value": "false",
    "description": "Set to true to require email verification on signup."
  }
}
```

---

## 5. Re-create draft command (NOT auto-publish, per AGENTS.md rule 3)

The sibling-service pattern changes the template's service topology (now 3 sibling services instead of 2 siblings + 1 plugin). Railway's `templateUpdate` mutation does NOT exist — to capture the new topology you must delete the existing draft and re-create from a fresh test project.

```bash
# Helper: resolve service IDs from the test project
get_svc_id() { railway service list --json | jq -r ".[] | select(.name==\"$1\") | .id"; }
PG_ID=$(get_svc_id "postgres")
CLICKHOUSE_ID=$(get_svc_id "ClickHouse")
PLAUSIBLE_ID=$(get_svc_id "Plausible CE")
echo "postgres=$PG_ID  clickhouse=$CLICKHOUSE_ID  plausible=$PLAUSIBLE_ID"

# 1. Delete the existing f0NGX9 draft (cannot be re-published in-place)
railway templates delete f0NGX9 --workspace INAPP --yes 2>&1 || true

# 2. Build a fresh multi-service test project in railway-plausible/
cd railway-plausible && railway up . --new --project plausible-test-sibling --yes 2>&1 | tail -10
cd /var/home/ihshim523/Work/railway

# 3. Add the Postgres sibling service (NON-interactive)
railway add --image postgres:16-alpine --service postgres 2>&1 | tail -5
PG_ID=$(get_svc_id "postgres")

# 4. Register the Postgres sibling service volume + vars
railway volume add --service "$PG_ID" --mount-path /var/lib/postgresql
railway variables set --service "$PG_ID" \
  POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres \
  POSTGRES_DB=plausible PGDATA=/var/lib/postgresql/data --kv
echo "  Volume mount created:"
railway volume list --json | jq -r ".volumes[] | select(.serviceId==\"$PG_ID\") | \"    mountPath=\(.mountPath)\""

# 5. Wait ~30s for Postgres initdb, then redeploy Plausible CE so migrations run
sleep 30
PLAUSIBLE_ID=$(get_svc_id "Plausible CE")
railway service redeploy --service "$PLAUSIBLE_ID" --yes

# 6. Create new template draft from the test project
railway templates create --project plausible-test-sibling --json | tee /tmp/template-draft.json

> ⚠️ **WARNING — UNPUBLISHED drafts skip auto-domain generation (verified 2026-07-08 on `zippy-elegance` deploy of draft `-Z5F9M`).**
>
> Deploying via `railway deploy --template <new-code> --new` from an UNPUBLISHED draft creates services but does **NOT** auto-generate `*.up.railway.app` subdomains. The deploy will succeed, but `BASE_URL` will resolve to literally `https://` (empty domain), `railway domain list` will show zero domains on the Plausible CE service, and Plausible CE will fail to boot (HTTP 502 on `/api/health`) because its public-URL requirement is unsatisfied.
>
> The dashboard click-to-deploy flow invokes the backend `serviceDomainCreate` mutation per service; programmatic `railway deploy --template` does not. This is undocumented behavior — the only fixes are:
>
> 1. **Publish the template** (`railway templates publish <new-code>` after section 6 smoke-test passes). Marketplace-published templates re-enable auto-domain generation, so deploys from the marketplace URL self-resolve `${{RAILWAY_PUBLIC_DOMAIN}}` without manual intervention.
> 2. **For the publish-source test project only**, generate the domain manually:
>    ```bash
>    railway service link "<plausible-ce-service-id>" && railway domain
>    DOMAIN=$(railway domain list --json | jq -r '.domains[0].domain // .[0].domain // empty')
>    railway variables set "BASE_URL=https://${DOMAIN}"
>    railway service redeploy --service "<plausible-ce-service-id>" --yes
>    ```
>    Brittle — does not propagate to users deploying from the marketplace URL.
>
> **Recommendation:** do not ship a marketplace-published template without verifying both paths. If smoke-test section 6 shows the deploy works WITHOUT manual domain steps, the template is truly marketplace-ready. If it still requires the manual CLI recipe (option 2), the template is not yet publishable.

# 7. **CRITICAL VERIFICATION** — confirm volumeMounts serialized into template
#    Skill ref caveat: UI widget volumeMounts MAY not propagate to marketplace deploys.
#    If the volume widget does not serialize into the captured template's root-level
#    serializedConfig, a fresh marketplace deploy would receive no volume — silent data
#    loss on every restart.
#
#    Run this graphQL query to inspect serializedConfig.services.<pg-id>.volumeMounts:
TEMPLATE_ID=$(jq -r '.id' /tmp/template-draft.json)
echo "Inspect template $TEMPLATE_ID for volumeMounts on the postgres service:"
railway graphql <<EOF
query {
  template(id: "$TEMPLATE_ID") {
    serializedConfig
  }
}
EOF
#    EXPECTED output (look for "mountPath": "/var/lib/postgresql" on the postgres service):
#      "services": {
#        "<postgres-uuid>": {
#          "name": "postgres",
#          "volumeMounts": { "/var/lib/postgresql": { "name": "postgres-volume", "sizeMB": 5000 } }
#        }
#      }
#
#    IF volumeMounts is MISSING in serializedConfig, the dashboard-paste.md recipe is
#    incomplete: marketplace deploys will not auto-create the volume. Mitigation options
#    (after the fact):
#      A. Edit the template's root-level Raw JSON in the dashboard editor to inject
#         the volumeMount manually into the postgres service's serializedConfig.
#      B. Switch to IaC (.railway/railway.ts) and re-create the template — IaC encodes
#         volumeMounts as the source-of-truth.
#      C. Post-deploy manual: railway volume add --service <id> --mount-path /var/lib/postgresql
#         after every marketplace deploy. Brittle.
#      D. **templateVolumeUpdate mutation** (programmatic) — call Railway's graphQL
#         templateVolumeUpdate to inject the volumeMount on the postgres service directly:
#         railway graphql <<'GRAPHQL'
#         query($input: TemplateVolumeUpdateInput!) {
#           templateVolumeUpdate(input: $input)
#         }
#         GRAPHQL
#         then run with --variables '{"input":{"templateId":"'$TEMPLATE_ID'","serviceName":"postgres","mountPath":"/var/lib/postgresql","sizeMB":5000}}'
#         Cleanest of the four paths if your CI supports it; doesn't require regenerating from IaC.
```

DO NOT proceed to `railway templates publish <new-code>` until smoke-tested end-to-end.

---

## 6. Smoke-test deployment (after re-creating draft)

After re-creating the draft, deploy from a fresh ephemeral env:

```bash
# Deploy to a fresh ephemeral env via the new draft template code
railway deploy --template <new-code> --new
```

Verifications:

```bash
# 1. All three services report Online
railway status | grep -E "Plausible CE|ClickHouse|postgres"

# 2. Postgres vars match literal defaults (no random secrets injected)
railway variables --service Postgres --kv | grep -E '^(POSTGRES_|PGDATA)='
#   Expect:
#     POSTGRES_USER=postgres
#     POSTGRES_PASSWORD=postgres
#     POSTGRES_DB=plausible
#     PGDATA=/var/lib/postgresql/data

# 3. Volume mounted at parent path (NOT directly at PGDATA)
railway volume list --json | python3 -c "import json,sys; [print(f'  {v[\"name\"]} mountPath={v.get(\"mountPath\")}') for v in json.load(sys.stdin).get('volumes',[])]"
#   Expect: postgres-volume mountPath=/var/lib/postgresql   (NOT /var/lib/postgresql/data)

# 4. ClickHouse vars match literal defaults
railway variables --service ClickHouse --kv | grep -E '^(CLICKHOUSE_)'
#   Expect:
#     CLICKHOUSE_USER=plausible
#     CLICKHOUSE_PASSWORD=plausible2026
#     CLICKHOUSE_DB=plausible

# 5. Plausible CE's DATABASE_URL points to sibling postgres service
railway variables --service "Plausible CE" --kv | grep -E '^(DATABASE_URL|BASE_URL|SECRET_KEY_BASE|CLICKHOUSE_DATABASE_URL)'
#   Expect: DATABASE_URL=postgresql://postgres:postgres@postgres.railway.internal:5432/plausible

# 6. Plausible migration succeeded (no ECONNREFUSED on Postgres)
railway logs --service "Plausible CE" | grep -iE 'schema_migrations|migrated|started' | tail -20
#   Expect: "Migrations successful" or similar, NO ECONNREFUSED lines

# 7. HTTP health
domain=$(railway domain --service "Plausible CE")
curl -s -o /dev/null -w "%{http_code}\n" "https://${domain}/api/health"
#   Expect: 200
```

---

## Troubleshooting reference

- **PGDATA crash loop** on Postgres service: confirm the Volume widget mount path is `/var/lib/postgresql` (NOT `/var/lib/postgresql/data`). The latter traps `lost+found/` inside PGDATA → initdb errors with `directory exists but is not empty`. The former places `lost+found/` at the volume root, outside PGDATA, and initdb sees an empty dir.
- **Connection refused Postgres**: usually the volume wasn't created in section 1, or the volume mount path is wrong. Run `railway volume list --json` to verify.
- **Auth failure** on ClickHouse or Postgres: literal default passwords used in this paste (`postgres`/`postgres`, `plausible`/`plausible2026`). If customized, update both the credential tile AND the Plausible CE tile's corresponding URL.
- **BASE_URL errors**: literal `https://${RAILWAY_PUBLIC_DOMAIN}` form. Plausible requires the `https://` prefix — do NOT drop it.
- **Template still shows old service topology after re-create draft**: Railway has no mutation to update template service topology in place — must delete + re-create.
- **Plausible CE service has no auto-generated `*.up.railway.app` domain** after deploying via `railway deploy --template`: the template is UNPUBLISHED. Programmatic deploy-from-draft skips the dashboard's `serviceDomainCreate` step. Fix: publish the template (recommended), or generate the domain manually via `railway service link "<plausible-ce-id>" && railway domain` (only works for the publish-source project; marketplace users still need the published template). Verified on `zippy-elegance` 2026-07-08 — see section 5 WARNING for details.

File generated 2026-07-08 after Path B sibling-service refactor.
