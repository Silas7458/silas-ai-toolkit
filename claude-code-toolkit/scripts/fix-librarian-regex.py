"""Fix librarian date regex to match any YYYY-MM-DD in message block."""
import json, os, urllib.request

N8N_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMGVjNzM3ZC1iMDFhLTQ2MjktODg5OC01ZTQ3ZTA1YTJmMWEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiOTgwMWFlZTItMzg5Ni00NjZiLWFmYzMtNDY5NjJkNGZhMWJkIiwiaWF0IjoxNzcxODAyNTMzfQ.xzmBnPtuC3MNyGyjt8rIoqvTY4BawXUeXonncPcsMxs"
BASE = "http://localhost:5678/api/v1"

# Step 1: Fetch
req = urllib.request.Request(f"{BASE}/workflows/AUTO_LIBRARIAN_001", headers={"X-N8N-API-KEY": N8N_KEY})
with urllib.request.urlopen(req) as resp:
    wf = json.loads(resp.read())

# Step 2: Fix the regex
for node in wf.get('nodes', []):
    if node['name'] == 'File Maintenance':
        code = node['parameters']['jsCode']
        # The old pattern: /##\s+(\d{4}-\d{2}-\d{2})/
        # The new pattern: /(\d{4}-\d{2}-\d{2})/
        # In the JS code string, \s and \d are literal backslash-s and backslash-d
        old_pattern = r'/##\s+(\d{4}-\d{2}-\d{2})/'
        new_pattern = r'/(\d{4}-\d{2}-\d{2})/'
        if old_pattern in code:
            code = code.replace(old_pattern, new_pattern)
            node['parameters']['jsCode'] = code
            print(f"SUCCESS: Replaced regex")
            # Verify
            for line in code.split('\n'):
                if 'dateMatch' in line and 'match' in line:
                    print(f"  New line: {line.strip()}")
        else:
            print(f"WARNING: Old pattern not found in code")
            # Debug: show the actual dateMatch line
            for line in code.split('\n'):
                if 'dateMatch' in line and 'match' in line:
                    print(f"  Actual line: {repr(line.strip())}")
        break

# Step 3: Save fixed JSON — use curl to push (urllib fights n8n API)
temp = os.environ.get('TEMP', '/tmp')
outpath = os.path.join(temp, 'lib-regex-fixed.json')
with open(outpath, 'w') as f:
    json.dump(wf, f)
print(f"Saved fixed JSON to {outpath}")
print("Run: curl -X PUT with this file, then reactivate")
