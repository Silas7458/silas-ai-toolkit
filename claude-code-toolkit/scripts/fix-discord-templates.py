"""Fix Discord webhook template expressions in all 4 n8n workflows."""
import json, urllib.request

N8N_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMGVjNzM3ZC1iMDFhLTQ2MjktODg5OC01ZTQ3ZTA1YTJmMWEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiOTgwMWFlZTItMzg5Ni00NjZiLWFmYzMtNDY5NjJkNGZhMWJkIiwiaWF0IjoxNzcxODAyNTMzfQ.xzmBnPtuC3MNyGyjt8rIoqvTY4BawXUeXonncPcsMxs"
BASE = "http://localhost:5678/api/v1"

# Map: workflow_id -> {node_name: new jsonBody expression}
FIXES = {
    "z4yzjnt39FQJID0S": {  # Heartbeat Monitor
        "Discord: Alert Heartbeat": '={{ JSON.stringify({content: "**[Heartbeat Monitor]** Infrastructure alert\\n" + ($json.failures_summary || $json.message || "Health check failures detected")}) }}'
    },
    "hD0Kh4mxu8cLoOwl": {  # Error Handler
        "Discord: Alert Failure": '={{ JSON.stringify({content: "**[Error Handler]** Workflow failure\\n" + ($json.error_summary || $json.message || "An n8n workflow error occurred")}) }}'
    },
    "cNRy2M4RaAL6usIo": {  # Daily Health Check
        "Discord: Alert Health": '={{ JSON.stringify({content: "**[Health Check]** Issues detected\\n" + ($json.issues || $json.report || "Daily health check found problems")}) }}'
    },
    "08WM371MryB61MGT": {  # Deliberation Pipeline
        "Discord: Post Decision": '={{ JSON.stringify({content: "**[Council Decision]** Deliberation complete\\nTopic: " + ($json.task_brief || $json.topic || "unknown") + "\\nConfidence: " + ($json.confidence || "N/A") + "\\nSynthesis: " + (($json.synthesis || "See full results").substring(0, 1500))}) }}'
    }
}

for wf_id, node_fixes in FIXES.items():
    # Fetch
    req = urllib.request.Request(f"{BASE}/workflows/{wf_id}", headers={"X-N8N-API-KEY": N8N_KEY})
    with urllib.request.urlopen(req) as resp:
        wf = json.loads(resp.read())

    print(f"\n=== {wf['name']} ===")
    changed = False

    for node in wf['nodes']:
        if node['name'] in node_fixes:
            old_body = node['parameters'].get('jsonBody', '')
            node['parameters']['jsonBody'] = node_fixes[node['name']]
            print(f"  Fixed: {node['name']}")
            changed = True

    if not changed:
        print("  No matching nodes found, skipping")
        continue

    # Push (required fields: name, nodes, connections, settings)
    clean = {k: wf[k] for k in ['name', 'nodes', 'connections', 'settings'] if k in wf}
    data = json.dumps(clean).encode()
    req2 = urllib.request.Request(f"{BASE}/workflows/{wf_id}", data=data,
        headers={"X-N8N-API-KEY": N8N_KEY, "Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req2) as resp2:
        r = json.loads(resp2.read())
        print(f"  Pushed: active={r.get('active')}")
