"""Check n8n workflows for Discord webhook URLs and nodes."""
import json, sys, re, urllib.request

N8N_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
WF_IDS = ["08WM371MryB61MGT", "hD0Kh4mxu8cLoOwl", "z4yzjnt39FQJID0S", "cNRy2M4RaAL6usIo"]

for wf_id in WF_IDS:
    req = urllib.request.Request(
        f"http://localhost:5678/api/v1/workflows/{wf_id}",
        headers={"X-N8N-API-KEY": N8N_KEY}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    print(f"=== {data.get('name', '?')} ({wf_id}) ===")
    wf_str = json.dumps(data)

    # Find discord webhook URLs
    webhooks = re.findall(r'https://discord[.]com/api/webhooks/[^"\s]+', wf_str)

    # Find Discord-related nodes
    for node in data.get('nodes', []):
        node_str = json.dumps(node).lower()
        if 'discord' in node_str:
            print(f"  Discord Node: {node['name']} | Type: {node['type']}")
            params = node.get('parameters', {})
            url = params.get('url', '')
            if url:
                print(f"    URL: {url}")
            js = params.get('jsCode', '')
            if 'discord' in js.lower():
                # Extract webhook URL from code
                code_webhooks = re.findall(r'https://discord[.]com/api/webhooks/[^"\s\']+', js)
                for wh in code_webhooks:
                    print(f"    Code webhook: {wh}")

    if webhooks:
        for wh in set(webhooks):
            print(f"  Webhook URL: {wh}")

    if not webhooks and not any('discord' in json.dumps(n).lower() for n in data.get('nodes', [])):
        print("  No Discord integration found")
    print()
