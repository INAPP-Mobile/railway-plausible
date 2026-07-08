#!/usr/bin/env python3
"""Build multi-service Plausible project and generate template."""
import json
import sys
import urllib.request
import urllib.error

TOKEN = open("/var/home/ihshim523/.railway/api-token").read().strip()
ENDPOINT = "https://backbone.railway.app/graphql/v2"


def graphql(query, variables=None):
    data = {"query": query, "variables": variables or {}}
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(data).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": f"HTTP {e.code}", "body": body}


# Step 1: Create a new project
print("=== Creating new project ===")
create_proj = """mutation ($name: String!, $workspaceId: String!) {
  projectCreate(input: {name: $name, workspaceId: $workspaceId}) {
    id
    primaryEnvironmentId
  }
}"""

# Get the user's workspace ID first
me_q = """query {
  project(id: "5cd8c46d-126f-47ff-bcc4-49400d068b36") {
    workspace { id }
  }
}"""
me_r = graphql(me_q)
workspace_id = me_r["data"]["project"]["workspace"]["id"]
print(f"Workspace ID: {workspace_id}")

proj_r = graphql(create_proj, {"name": "plausible-3svc", "workspaceId": workspace_id})
if proj_r.get("error"):
    print("ERROR creating project:", json.dumps(proj_r, indent=2))
    sys.exit(1)

project_id = proj_r["data"]["projectCreate"]["id"]
env_id = proj_r["data"]["projectCreate"]["primaryEnvironmentId"]
print(f"Project ID: {project_id}")
print(f"Environment ID: {env_id}")

# Step 2: Create PostgreSQL service
print("\n=== Creating PostgreSQL service ===")
create_pg = """mutation ($input: ServiceCreateInput!) {
  serviceCreate(input: $input) {
    id name
  }
}"""
pg_r = graphql(create_pg, {"input": {
    "projectId": project_id,
    "environmentId": env_id,
    "name": "Postgres",
    "source": {"image": "ghcr.io/railwayapp-templates/postgres-ssl:18"},
    "icon": "https://devicons.railway.app/i/postgresql.svg"
}})
if pg_r.get("error"):
    print("ERROR creating postgres:", json.dumps(pg_r, indent=2))
    sys.exit(1)
pg_id = pg_r["data"]["serviceCreate"]["id"]
print(f"Postgres service ID: {pg_id}")

# Step 3: Create ClickHouse service
print("\n=== Creating ClickHouse service ===")
ch_r = graphql(create_pg, {"input": {
    "projectId": project_id,
    "environmentId": env_id,
    "name": "ClickHouse",
    "source": {"repo": "https://github.com/INAPP-Mobile/railway-plausible", "rootDirectory": "clickhouse"},
    "icon": "https://devicons.railway.app/i/clickhouse.svg"
}})
if ch_r.get("error"):
    print("ERROR creating clickhouse:", json.dumps(ch_r, indent=2))
    sys.exit(1)
ch_id = ch_r["data"]["serviceCreate"]["id"]
print(f"ClickHouse service ID: {ch_id}")

# Step 4: Create Plausible CE service
print("\n=== Creating Plausible CE service ===")
pl_r = graphql(create_pg, {"input": {
    "projectId": project_id,
    "environmentId": env_id,
    "name": "Plausible CE",
    "source": {"repo": "https://github.com/INAPP-Mobile/railway-plausible"},
    "icon": "https://simpleicons.org/icons/plausibleanalytics.svg"
}})
if pl_r.get("error"):
    print("ERROR creating plausible:", json.dumps(pl_r, indent=2))
    sys.exit(1)
pl_id = pl_r["data"]["serviceCreate"]["id"]
print(f"Plausible CE service ID: {pl_id}")

# Step 5: Update Plausible CE service with variables and healthcheck
print("\n=== Updating Plausible CE service ===")
update_svc = """mutation ($input: ServiceUpdateInput!) {
  serviceUpdate(input: $input) {
    id name
  }
}"""
# We need to set env vars referencing the other services
pl_update_r = graphql(update_svc, {"input": {
    "id": pl_id,
    "deploy": {
        "healthcheckPath": "/api/health",
        "healthcheckTimeout": 60,
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10
    },
    "variables": {
        "BASE_URL": {"value": "${{RAILWAY_PUBLIC_DOMAIN}}"},
        "SECRET_KEY_BASE": {"value": "${{secret(64)}}"},
        "DATABASE_URL": {"value": "${{Postgres.DATABASE_URL}}"},
        "CLICKHOUSE_DATABASE_URL": {"value": "http://clickhouse:8123/plausible"},
        "DISABLE_REGISTRATION": {"value": "false"},
        "ENABLE_EMAIL_VERIFICATION": {"value": "false"},
    }
}})
if pl_update_r.get("error"):
    print("ERROR updating plausible:", json.dumps(pl_update_r, indent=2))
    sys.exit(1)
print("Plausible CE service updated")

# Step 6: Update ClickHouse service with healthcheck and volume
print("\n=== Updating ClickHouse service ===")
ch_update_r = graphql(update_svc, {"input": {
    "id": ch_id,
    "deploy": {
        "healthcheckPath": "/ping",
        "healthcheckTimeout": 30,
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10
    },
    "variables": {
        "CLICKHOUSE_DB": {"value": "plausible", "description": "Default database name"},
        "CLICKHOUSE_USER": {"value": "plausible", "description": "ClickHouse user"},
        "CLICKHOUSE_PASSWORD": {"value": "${{secret(24)}}", "description": "ClickHouse password"},
    }
}})
if ch_update_r.get("error"):
    print("ERROR updating clickhouse:", json.dumps(ch_update_r, indent=2))
    sys.exit(1)
print("ClickHouse service updated")

# Step 7: Generate template
print("\n=== Generating template from project ===")
gen_tmpl = """mutation ($projectId: String!, $environmentId: String!) {
  templateGenerate(projectId: $projectId, environmentId: $environmentId) {
    id code name status serializedConfig
  }
}"""
gen_r = graphql(gen_tmpl, {"projectId": project_id, "environmentId": env_id})
if gen_r.get("error"):
    print("ERROR generating template:", json.dumps(gen_r, indent=2))
    sys.exit(1)

tmpl = gen_r["data"]["templateGenerate"]
print(f"Template ID: {tmpl['id']}")
print(f"Template Code: {tmpl['code']}")
print(f"Template Status: {tmpl['status']}")
print(f"SerializedConfig: {json.dumps(tmpl['serializedConfig'], indent=2)}")

print("\nDone!")
