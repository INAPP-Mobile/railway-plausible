#!/usr/bin/env python3
"""Helper for Railway template GraphQL API."""
import json
import sys
import urllib.request

TOKEN = open("/var/home/ihshim523/.railway/api-token").read().strip()
ENDPOINT = "https://backbone.railway.app/graphql/v2"


def graphql(query, variables=None):
    data = {"query": query}
    if variables:
        data["variables"] = variables
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


def get_template(tid):
    q = """query ($id: ID!) {
      template(id: $id) {
        id code name status serializedConfig
      }
    }"""
    return graphql(q, {"id": tid})


def delete_template(tid):
    q = """mutation ($id: ID!) {
      templateDelete(id: $id) {
        success
      }
    }"""
    return graphql(q, {"id": tid})


def template_generate(project_id, env_id):
    q = """mutation ($projectId: String!, $environmentId: String!) {
      templateGenerate(projectId: $projectId, environmentId: $environmentId) {
        id code name status serializedConfig
      }
    }"""
    return graphql(q, {"projectId": project_id, "environmentId": env_id})


def create_service(project_id, env_id, name, source_type, source_value, root_dir=None):
    """source_type: 'image' or 'repo'"""
    source_json = {}
    if source_type == "image":
        source_json = {"image": source_value}
    elif source_type == "repo":
        source_json = {"repo": source_value, "rootDirectory": root_dir}

    q = """mutation ($input: ServiceCreateInput!) {
      serviceCreate(input: $input) {
        id name
      }
    }"""
    return graphql(q, {"input": {
        "projectId": project_id,
        "environmentId": env_id,
        "name": name,
        "source": source_json,
    }})


def update_service(sid, **kwargs):
    q = """mutation ($input: ServiceUpdateInput!) {
      serviceUpdate(input: $input) {
        id name
      }
    }"""
    inp = {"id": sid}
    inp.update(kwargs)
    return graphql(q, {"input": inp})


def get_project_info(pid):
    q = """query ($id: ID!) {
      project(id: $id) {
        id name
        environment {
          id name
        }
        services {
          id name
        }
      }
    }"""
    return graphql(q, {"id": pid})


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "get":
        print(json.dumps(get_template(sys.argv[2]), indent=2))
    elif cmd == "delete":
        print(json.dumps(delete_template(sys.argv[2]), indent=2))
    elif cmd == "generate":
        print(json.dumps(template_generate(sys.argv[2], sys.argv[3]), indent=2))
    elif cmd == "project":
        print(json.dumps(get_project_info(sys.argv[2]), indent=2))
    elif cmd == "create-svc":
        # project_id, env_id, name, source_type, source_value, [root_dir]
        root = sys.argv[7] if len(sys.argv) > 7 else None
        print(json.dumps(create_service(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], root), indent=2))
    elif cmd == "update-svc":
        sid = sys.argv[2]
        # parse key=value pairs
        kwargs = {}
        for arg in sys.argv[3:]:
            k, v = arg.split("=", 1)
            kwargs[k] = v
        print(json.dumps(update_service(sid, **kwargs), indent=2))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
